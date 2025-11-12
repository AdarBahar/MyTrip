import { NextRequest } from 'next/server';
import { getApiBaseSync } from '@/lib/api/base';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  const apiBase = getApiBaseSync();
  const search = req.nextUrl.searchParams.toString();
  const target = `${apiBase}/location/live/sse${search ? `?${search}` : ''}`;

  const headers: Record<string, string> = {
    Accept: 'text/event-stream',
    Connection: 'keep-alive',
  };
  const token = process.env.LOC_API_TOKEN || process.env.NEXT_PUBLIC_LOC_API_TOKEN;
  if (token) headers['X-API-Token'] = token;

  const upstream = await fetch(target, {
    method: 'GET',
    headers,
    cache: 'no-store',
  });

  // Pass-through streaming body and key headers
  const resHeaders = new Headers(upstream.headers);
  resHeaders.set('Cache-Control', 'no-cache');
  resHeaders.set('Content-Type', 'text/event-stream; charset=utf-8');
  resHeaders.set('X-Accel-Buffering', 'no');

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: resHeaders,
  });
}
