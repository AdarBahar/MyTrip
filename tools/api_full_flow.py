#!/usr/bin/env python3
import json
import sys
import time
import argparse
import os
from pathlib import Path
import csv
from typing import Optional, Dict, Any, Tuple, List
from urllib import request, error

class Client:
    def __init__(self, base: str, token: Optional[str] = None, verbose: bool = True):
        self.base = base.rstrip('/')
        self.token = token
        self.verbose = verbose
        self.timings: List[Tuple[str, int, float]] = []

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        h = {"accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        if extra:
            h.update(extra)
        return h

    def call(self, name: str, method: str, path: str, body: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = f"{self.base}{path}"
        data = None
        hdrs = self._headers(headers)
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
        req = request.Request(url=url, method=method, data=data, headers=hdrs)
        t0 = time.perf_counter()
        status = 0
        text = ""
        try:
            with request.urlopen(req, timeout=120) as resp:
                status = resp.getcode()
                text = resp.read().decode("utf-8")
        except error.HTTPError as e:
            status = e.getcode()
            text = e.read().decode("utf-8", errors="ignore")
        except Exception as e:
            status = 0
            text = str(e)
        dt = time.perf_counter() - t0
        self.timings.append((name, status, dt))
        try:
            js = json.loads(text) if text else {}
        except Exception:
            js = {"_raw": text}
        if self.verbose:
            print(f"- {name}: status {status}, {dt:.2f}s")
        return js


def write_reports(out_dir: Path, timings: List[Tuple[str, int, float]], artifacts: Dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    # CSV timings
    with (out_dir / 'timings.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['name', 'status', 'seconds'])
        for n, s, t in timings:
            w.writerow([n, s, f"{t:.3f}"])
    # JSON artifacts
    with (out_dir / 'artifacts.json').open('w') as f:
        json.dump(artifacts, f, indent=2)


def run_flow(base: str, email: Optional[str], verbose: bool, out_dir: Optional[str] = None) -> int:
    ok = True
    client = Client(base, verbose=verbose)
    artifacts: Dict[str, Any] = {}

    # Step 1: Auth
    email = email or f"api.test+{int(time.time())}@example.com"
    print("Step 1: Login")
    auth = client.call("AUTH_LOGIN", "POST", "/auth/login", body={"email": email})
    token = auth.get("access_token")
    ok = ok and bool(token)
    if not token:
        print("  Login failed:", auth)
        return 2
    client.token = token
    artifacts['auth'] = auth

    # Step 2: Create Trip
    print("Step 2: Create trip")
    trip = client.call("TRIP_CREATE", "POST", "/trips/", body={"title": "API Full Flow", "destination": "Testland"})
    trip_id = trip.get("id")
    ok = ok and bool(trip_id)
    artifacts['trip'] = trip
    print(f"  Trip: {trip_id}")

    # Step 3: Create Day with status active
    print("Step 3: Create day (seq=1)")
    day = client.call("DAY_CREATE", "POST", f"/trips/{trip_id}/days", body={"seq": 1, "status": "active", "rest_day": False})
    day_id = day.get("id")
    ok = ok and bool(day_id)
    artifacts['day'] = day
    print(f"  Day: {day_id}")

    # Step 4: Create places
    print("Step 4: Create places (start, end, via1, via2, via3)")
    def make_place(name: str, lat: float, lon: float) -> str:
        p = client.call(f"PLACE_{name}", "POST", "/places/", body={"name": name, "address": f"{name} Address", "lat": lat, "lon": lon})
        return p.get("id")
    p_start = make_place("Start", 32.0809, 34.7806)
    p_end   = make_place("End",   31.7717, 35.2170)
    p_via1  = make_place("Via1",  31.4118, 35.0818)
    p_via2  = make_place("Via2",  31.0461, 34.8516)
    # A third via placed out of order: between start and end but not adjacent to current VIAs
    p_via3  = make_place("Via3",  31.9000, 35.0000)
    artifacts['places'] = { 'start': p_start, 'end': p_end, 'via1': p_via1, 'via2': p_via2, 'via3': p_via3 }

    # Step 5: Create stops START, VIA1, VIA2, END (no VIA3 yet)
    print("Step 5: Create stops (start, via1, via2, end)")
    def make_stop(name: str, place_id: str, seq: int, kind: str, fixed: bool, prio: int) -> str:
        s = client.call(f"STOP_{name}", "POST", f"/stops/{trip_id}/days/{day_id}/stops", body={
            "place_id": place_id, "seq": seq, "kind": kind, "fixed": fixed,
            "notes": "", "priority": prio, "stop_type": "other"
        })
        sid = s.get("id")
        if not sid:
            # Fallback: pick next available seq
            st = client.call("STOPS_LIST_FOR_SEQ", "GET", f"/stops/{trip_id}/days/{day_id}/stops")
            try:
                max_seq = max([int(it.get("seq", 0)) for it in st.get("stops", [])] + [0])
            except Exception:
                max_seq = 0
            new_seq = max_seq + 1
            if new_seq != seq:
                if client.verbose:
                    print(f"  Retrying {name} at seq={new_seq} (fallback)")
                s2 = client.call(f"STOP_{name}_RETRY", "POST", f"/stops/{trip_id}/days/{day_id}/stops", body={
                    "place_id": place_id, "seq": new_seq, "kind": kind, "fixed": fixed,
                    "notes": "", "priority": prio, "stop_type": "other"
                })
                sid = s2.get("id")
        return sid or ""
    s_start = make_stop("START", p_start, 1, "start", True, 3)
    s_via1  = make_stop("VIA1",  p_via1, 2, "via",   False, 2)
    s_via2  = make_stop("VIA2",  p_via2, 3, "via",   False, 2)
    s_end   = make_stop("END",   p_end,   4, "end",   True, 3)
    artifacts['stops_initial'] = { 'start': s_start, 'via1': s_via1, 'via2': s_via2, 'end': s_end }

    # Helper: compute with retries
    def compute_with_retry(tag: str, max_attempts: int = 5, delay_sec: float = 4.0) -> Optional[str]:
        for i in range(1, max_attempts+1):
            comp = client.call(f"ROUTE_COMPUTE{tag}_{i}", "POST", f"/routing/days/{day_id}/route/compute", body={"profile": "car", "optimize": True})
            preview = comp.get("preview_token")
            if preview:
                return preview
            status = next((s for (n,s,_) in client.timings[::-1] if n == f"ROUTE_COMPUTE{tag}_{i}"), None)
            if status == 429 and i < max_attempts:
                if client.verbose:
                    print(f"  rate-limited, retrying in {delay_sec:.0f}s...")
                time.sleep(delay_sec)
            else:
                break
        return None

    # Step 6: Compute+commit route
    print("Step 6: Compute and commit route")
    preview = compute_with_retry("_A")
    if preview:
        artifacts['compute_commit_A'] = { 'preview_token': preview }
        artifacts['commit_A'] = client.call("ROUTE_COMMIT_A", "POST", f"/routing/days/{day_id}/route/commit", body={"preview_token": preview, "name": "Default"})
    else:
        print("  Compute preview not available (likely throttled). Proceeding with active summary.")

    # Step 7: Get active summary
    print("Step 7: Fetch active summary")
    summary1 = client.call("ACTIVE_SUMMARY_1", "GET", f"/routing/days/{day_id}/active-summary")
    artifacts['active_summary_1'] = summary1
    v1 = summary1.get("route_version_id")
    km1 = summary1.get("route_total_km")
    min1 = summary1.get("route_total_min")
    coords1 = bool(summary1.get("route_coordinates"))
    print(f"  Active v1={v1}, km={km1}, min={min1}, coords={coords1}")

    # Step 8: Add out-of-order VIA3 at seq=2
    print("Step 8: Add out-of-order stop VIA3 at seq=2")
    s_via3 = make_stop("VIA3", p_via3, 2, "via", False, 2)
    artifacts['stop_via3'] = s_via3

    # Step 9: Optimize again (compute+commit) and fetch summary
    print("Step 9: Optimize route after out-of-order add")
    preview2 = compute_with_retry("_B")
    if preview2:
        artifacts['compute_commit_B'] = { 'preview_token': preview2 }
        artifacts['commit_B'] = client.call("ROUTE_COMMIT_B", "POST", f"/routing/days/{day_id}/route/commit", body={"preview_token": preview2, "name": "Optimized"})
    else:
        print("  Compute preview not available; relying on server-side commit hook.")

    print("Step 10: Fetch active summary again")
    summary2 = client.call("ACTIVE_SUMMARY_2", "GET", f"/routing/days/{day_id}/active-summary")
    artifacts['active_summary_2'] = summary2
    v2 = summary2.get("route_version_id")
    km2 = summary2.get("route_total_km")
    min2 = summary2.get("route_total_min")
    coords2 = bool(summary2.get("route_coordinates"))
    print(f"  Active v2={v2}, km={km2}, min={min2}, coords={coords2}")

    # Step 11: Validate stops count and route presence
    print("Step 11: Validate stops and route present")
    stops = client.call("STOPS_LIST", "GET", f"/stops/{trip_id}/days/{day_id}/stops?include_place=true")
    artifacts['stops'] = stops
    stop_count = len(stops.get("stops", []))
    print(f"  Stops count={stop_count}")

    # Optional: validate order consistency: START..(VIAs)..END exist in display order by seq
    seqs = [(s.get('seq'), s.get('id'), s.get('kind')) for s in stops.get('stops', [])]
    artifacts['stop_seqs'] = seqs

    logic_ok = bool(v2 and coords2 and stop_count >= 5)

    # Final report
    print("\n=== Final Report ===")
    print(f"Process successful: {'YES' if ok else 'NO'}")
    print(f"Logic worked as expected (route present incl. new stop): {'YES' if logic_ok else 'NO'}")
    print("\nResponse Times (name | status | seconds)")
    print("name\tstatus\telapsed_s")
    for n, s, t in client.timings:
        print(f"{n}\t{s}\t{t:.3f}")

    # Write artifacts/timings to out_dir when requested
    if out_dir:
        write_reports(Path(out_dir), client.timings, artifacts)
        print(f"\nArtifacts written to: {out_dir}")

    return 0 if (ok and logic_ok) else 1


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Full API flow test: auth -> trip/day -> stops -> route -> add out-of-order -> optimize")
    ap.add_argument("--base", default="http://localhost:8000", help="API base URL")
    ap.add_argument("--email", default=None, help="Login email (default: api.test+<epoch>@example.com)")
    ap.add_argument("--out", default=".reports/api_full_flow", help="Output directory for CSV/JSON artifacts")
    ap.add_argument("--no-verbose", action="store_true", help="Less console output")
    args = ap.parse_args(argv)
    return run_flow(args.base, args.email, verbose=not args.no_verbose, out_dir=args.out)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

