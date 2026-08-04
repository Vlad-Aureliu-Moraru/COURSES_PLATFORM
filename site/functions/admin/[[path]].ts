const BACKEND = 'http://167.172.45.10';

export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  const target = `${BACKEND}${url.pathname}${url.search}`;

  const headers = new Headers(request.headers);
  headers.set('Host', 'banionline.pages.dev');
  headers.set('X-Forwarded-Proto', 'https');
  headers.set('X-Forwarded-For', request.headers.get('CF-Connecting-IP') ?? '');

  const init = {
    method: request.method,
    headers,
    redirect: 'manual',
  };
  if (!['GET', 'HEAD'].includes(request.method)) {
    init.body = await request.arrayBuffer();
  }

  const upstream = await fetch(target, init);
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete('content-security-policy');
  responseHeaders.delete('x-frame-options');
  responseHeaders.set('Access-Control-Allow-Origin', '*');

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}
