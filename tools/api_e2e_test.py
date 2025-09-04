#!/usr/bin/env python3
import json
import sys
import time
import argparse
from typing import Optional, List, Tuple, Dict
from urllib import request, parse, error

class APITester:
    def __init__(self, base_url: str, token: Optional[str] = None, verbose: bool = True):
        self.base = base_url.rstrip('/')
        self.token = token
        self.results: List[Tuple[str, int, float]] = []  # (name, status, seconds)
        self.payloads: Dict[str, Dict] = {}
        self.verbose = verbose

    def _headers(self, extra: Optional[Dict] = None) -> Dict:
        h: Dict = {"accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        if extra:
            h.update(extra)
        return h

    def call(self, name: str, method: str, path: str, body: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        url = f"{self.base}{path}"
        data = None
        hdrs = self._headers(headers)
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
        req = request.Request(url=url, method=method, data=data, headers=hdrs)
        t0 = time.perf_counter()
        status = 0
        try:
            with request.urlopen(req, timeout=60) as resp:
                status = resp.getcode()
                text = resp.read().decode("utf-8")
        except error.HTTPError as e:
            status = e.getcode()
            text = e.read().decode("utf-8", errors="ignore")
        except Exception as e:
            status = 0
            text = str(e)
        dt = time.perf_counter() - t0
        self.results.append((name, status, dt))
        try:
            js = json.loads(text) if text else {}
        except Exception:
            js = {"_raw": text}
        self.payloads[name] = js
        if self.verbose:
            print(f"{name} | {status} | {dt:.3f}s")
        return js

    def get_result_table(self) -> str:
        lines = ["name\tstatus\telapsed_s"]
        for n, s, t in self.results:
            lines.append(f"{n}\t{s}\t{t:.3f}")
        return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Run API E2E tests against RoadTrip backend")
    ap.add_argument("--base", default="http://localhost:8000", help="API base URL (default: http://localhost:8000)")
    ap.add_argument("--email", default=None, help="Email to login with (default: api.test+<epoch>@example.com)")
    ap.add_argument("--no-verbose", action="store_true", help="Reduce console output")
    args = ap.parse_args(argv)

    email = args.email or f"api.test+{int(time.time())}@example.com"
    t = APITester(args.base, verbose=not args.no_verbose)

    # 0) Login
    login = t.call("AUTH_LOGIN", "POST", "/auth/login", body={"email": email})
    token = login.get("access_token")
    if not token:
        print("ERROR: login failed:", login)
        return 2
    t.token = token

    # 1) Create Trip
    trip = t.call("TRIP_CREATE", "POST", "/trips/", body={"title": "API Test Trip", "destination": "Testland"})
    trip_id = trip.get("id")
    if not trip_id:
        print("ERROR: trip create failed:", trip)
        return 2

    # 2) Create Day (seq 1)
    day = t.call("DAY_CREATE", "POST", f"/trips/{trip_id}/days", body={"seq": 1, "status": "active", "rest_day": False})
    day_id = day.get("id")
    if not day_id:
        print("ERROR: day create failed:", day)
        return 2

    # 3) Create 4 places (start, end, via1, via2)
    def create_place(name, addr, lat, lon):
        return t.call(f"PLACE_CREATE_{name}", "POST", "/places/", body={"name": name, "address": addr, "lat": lat, "lon": lon}).get("id")

    p_start = create_place("Start", "Start Address", 32.0809, 34.7806)
    p_end = create_place("End", "End Address", 31.7717, 35.2170)
    p_via1 = create_place("Via1", "Via1 Address", 31.4118, 35.0818)
    p_via2 = create_place("Via2", "Via2 Address", 31.0461, 34.8516)

    # 4) Create stops: start(seq1), via1(seq2), via2(seq3), end(seq4)
    def create_stop(label, place_id, seq, kind, fixed, priority):
        return t.call(f"STOP_CREATE_{label}", "POST", f"/stops/{trip_id}/days/{day_id}/stops", body={
            "place_id": place_id, "seq": seq, "kind": kind, "fixed": fixed,
            "notes": "", "priority": priority, "stop_type": "other"
        }).get("id")

    s_start = create_stop("START", p_start, 1, "start", True, 3)
    s_via1 = create_stop("VIA1", p_via1, 2, "via", False, 2)
    s_via2 = create_stop("VIA2", p_via2, 3, "via", False, 2)
    s_end = create_stop("END", p_end, 4, "end", True, 3)

    # 5) List stops include_place=true
    t.call("STOPS_LIST", "GET", f"/stops/{trip_id}/days/{day_id}/stops?include_place=true")

    # 6) Compute optimized route
    comp1 = t.call("ROUTE_COMPUTE", "POST", f"/routing/days/{day_id}/route/compute", body={"profile": "car", "optimize": True})
    preview = comp1.get("preview_token")

    # 7) Commit route
    if preview:
        t.call("ROUTE_COMMIT", "POST", f"/routing/days/{day_id}/route/commit", body={"preview_token": preview, "name": "Default"})

    # 8) Active summary
    t.call("ROUTE_ACTIVE_SUMMARY", "GET", f"/routing/days/{day_id}/active-summary")

    # 9) List routes
    t.call("ROUTES_LIST", "GET", f"/routing/days/{day_id}/routes")

    # 10) Reorder via stops (swap VIA order)
    t.call("STOPS_REORDER", "POST", f"/stops/{trip_id}/days/{day_id}/stops/reorder", body={
        "reorders": [
            {"stop_id": s_via2, "new_seq": 2},
            {"stop_id": s_via1, "new_seq": 3},
        ]
    })

    # 11) Compute+commit again
    comp2 = t.call("ROUTE_COMPUTE_2", "POST", f"/routing/days/{day_id}/route/compute", body={"profile": "car", "optimize": True})
    preview2 = comp2.get("preview_token")
    if preview2:
        t.call("ROUTE_COMMIT_2", "POST", f"/routing/days/{day_id}/route/commit", body={"preview_token": preview2})

    # 12) Final active summary
    t.call("ROUTE_ACTIVE_SUMMARY_2", "GET", f"/routing/days/{day_id}/active-summary")

    # --- Analysis Output ---
    stops = t.payloads.get("STOPS_LIST", {})
    comp1 = t.payloads.get("ROUTE_COMPUTE", {})
    sum1 = t.payloads.get("ROUTE_ACTIVE_SUMMARY", {})
    routes = t.payloads.get("ROUTES_LIST", {})
    comp2 = t.payloads.get("ROUTE_COMPUTE_2", {})
    sum2 = t.payloads.get("ROUTE_ACTIVE_SUMMARY_2", {})

    print("\n=== Analysis ===")
    print("Stops (include_place=true):", len(stops.get("stops", [])))
    print("Compute1 totals: km=", comp1.get("total_km"), " min=", comp1.get("total_min"), " preview?", bool(comp1.get("preview_token")))
    print("Active summary after commit1: version=", sum1.get("route_version_id"), " km=", sum1.get("route_total_km"), " min=", sum1.get("route_total_min"), " coords?", bool(sum1.get("route_coordinates")))
    active_routes = [r for r in routes.get("routes", []) if r.get("is_active")]
    print("Active route versions count:", len(active_routes))
    if active_routes:
        r = active_routes[0]
        print("Active route totals: km=", r.get("total_km"), " min=", r.get("total_min"))
    print("Compute2 totals: km=", comp2.get("total_km"), " min=", comp2.get("total_min"))
    print("Active summary after commit2: version=", sum2.get("route_version_id"), " km=", sum2.get("route_total_km"), " min=", sum2.get("route_total_min"), " coords?", bool(sum2.get("route_coordinates")))

    print("\n=== Response Times (name | status | seconds) ===")
    print(t.get_result_table())

    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

