#!/usr/bin/env python3
import hashlib, json, re, time
from pathlib import Path
from urllib.request import Request, urlopen

P = Path('chains/polygon-pos')
RPC_FILE = P / 'rpc_pool.txt'
PAIR_FILE = P / 'PAIR_UNIVERSE.jsonl'
TOKEN_FILE = P / 'TOKEN_UNIVERSE.jsonl'
DEX_FILE = P / 'DEX_UNIVERSE.json'
POOL_FILE = P / 'POOL_UNIVERSE.jsonl'

BATCH = 60
TIMEOUT = 35
MAX_ENDPOINTS = 2

def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

def load_jsonl(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def write_jsonl(path, rows):
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n')

def load_rpcs():
    out = []
    for line in RPC_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '|' not in line:
            continue
        name, url = line.split('|', 1)
        out.append((name.strip(), url.strip()))
    return out

def rpc_batch(url, calls):
    payload = [{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(calls)]
    req = Request(url, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
    with urlopen(req, timeout=TIMEOUT) as r:
        body = json.loads(r.read())
    if not isinstance(body, list):
        if len(calls) == 1 and isinstance(body, dict):
            return {0: body}
        raise RuntimeError('non-batch-response')
    return {int(x.get('id')): x for x in body if isinstance(x, dict) and isinstance(x.get('id'), int)}

def probe_endpoint(item):
    name, url = item
    try:
        rows = rpc_batch(url, [('eth_chainId', []), ('eth_blockNumber', [])])
        chain = rows.get(0, {}).get('result')
        block = rows.get(1, {}).get('result')
        if str(chain).lower() != '0x89' or not isinstance(block, str):
            return {'name': name, 'url': url, 'ok': False, 'reason': 'not_polygon'}
        return {'name': name, 'url': url, 'ok': True, 'block': block}
    except Exception as exc:
        return {'name': name, 'url': url, 'ok': False, 'reason': f'{type(exc).__name__}: {exc}'}

def decode_uint(raw):
    if not isinstance(raw, str) or not raw.startswith('0x') or len(raw[2:]) < 64:
        return None
    try:
        return int(raw[2:66], 16)
    except ValueError:
        return None

def decode_address(raw):
    if not isinstance(raw, str) or not raw.startswith('0x') or len(raw[2:]) < 64:
        return None
    return '0x' + raw[2:][-40:].lower()

def decode_string(raw):
    if not isinstance(raw, str) or not raw.startswith('0x'):
        return None
    h = raw[2:]
    if len(h) == 64:
        try:
            s = bytes.fromhex(h).rstrip(b'\\x00').decode('utf-8', errors='ignore').strip()
            return s or None
        except ValueError:
            return None
    try:
        if len(h) >= 128:
            offset = int(h[:64], 16) * 2
            if offset + 64 <= len(h):
                n = int(h[offset:offset+64], 16)
                b = bytes.fromhex(h[offset+64:offset+64+n*2])
                s = b.decode('utf-8', errors='ignore').strip()
                return s or None
    except (ValueError, UnicodeError):
        pass
    return None

def code_sha(raw):
    if not isinstance(raw, str) or not raw.startswith('0x'):
        return None
    try:
        return hashlib.sha256(bytes.fromhex(raw[2:])).hexdigest()
    except ValueError:
        return None

def normalized(v):
    return str(v or '').lower()

def enrich_tokens(tokens, endpoints):
    by_addr = {normalized(x.get('address')): x for x in tokens}
    addresses = sorted(a for a in by_addr if re.fullmatch(r'0x[a-f0-9]{40}', a))
    observations = {a: [] for a in addresses}
    for ep_name, url in endpoints:
        for off in range(0, len(addresses), max(1, BATCH // 4)):
            chunk = addresses[off:off + max(1, BATCH // 4)]
            calls = []
            kinds = []
            for a in chunk:
                calls.append(('eth_getCode', [a, 'latest'])); kinds.append((a, 'code'))
                for kind, sel in [('decimals','0x313ce567'), ('symbol','0x95d89b41'), ('name','0x06fdde03')]:
                    calls.append(('eth_call', [{'to': a, 'data': sel}, 'latest'])); kinds.append((a, kind))
            try:
                rows = rpc_batch(url, calls)
            except Exception as exc:
                for a in chunk:
                    observations[a].append({'endpoint': ep_name, 'error': f'{type(exc).__name__}: {exc}'})
                continue
            tmp = {a: {} for a in chunk}
            for i, (a, kind) in enumerate(kinds):
                tmp[a][kind] = rows.get(i, {}).get('result')
            for a in chunk:
                t = tmp[a]
                observations[a].append({
                    'endpoint': ep_name,
                    'code_sha256': code_sha(t.get('code')),
                    'code_bytes': (len(t.get('code','')) - 2) // 2 if isinstance(t.get('code'), str) and t.get('code','').startswith('0x') else None,
                    'decimals': decode_uint(t.get('decimals')),
                    'symbol': decode_string(t.get('symbol')),
                    'name': decode_string(t.get('name')),
                })
    for a in addresses:
        row = by_addr[a]
        obs = [x for x in observations[a] if x.get('code_sha256')]
        code_set = {x.get('code_sha256') for x in obs}
        row['onchain_identity'] = {
            'status': 'VERIFIED_MULTI_RPC' if len(obs) >= 2 and len(code_set) == 1 else ('VERIFIED_SINGLE_RPC' if obs else 'BLOCKED'),
            'observations': obs,
        }
        if obs:
            base = obs[0]
            for k in ('code_sha256','code_bytes','decimals','symbol','name'):
                row['static_' + k] = base.get(k)
    return tokens

def enrich_pairs(pairs, endpoints):
    by_addr = {normalized(x.get('pair_address') or x.get('pairAddress')): x for x in pairs}
    addresses = sorted(a for a in by_addr if re.fullmatch(r'0x[a-f0-9]{40}', a))
    observations = {a: [] for a in addresses}
    selectors = {
        'token0': '0x0dfe1681', 'token1': '0xd21220a7', 'factory': '0xc45a0155',
        'reserves': '0x0902f1ac', 'slot0': '0x3850c7bd', 'liquidity': '0x1a686502', 'fee': '0xddca3f43',
    }
    for ep_name, url in endpoints:
        for off in range(0, len(addresses), max(1, BATCH // 8)):
            chunk = addresses[off:off + max(1, BATCH // 8)]
            calls = []
            kinds = []
            for a in chunk:
                calls.append(('eth_getCode', [a, 'latest'])); kinds.append((a, 'code'))
                for kind, sel in selectors.items():
                    calls.append(('eth_call', [{'to': a, 'data': sel}, 'latest'])); kinds.append((a, kind))
            try:
                rows = rpc_batch(url, calls)
            except Exception as exc:
                for a in chunk:
                    observations[a].append({'endpoint': ep_name, 'error': f'{type(exc).__name__}: {exc}'})
                continue
            tmp = {a: {} for a in chunk}
            for i, (a, kind) in enumerate(kinds):
                tmp[a][kind] = rows.get(i, {}).get('result')
            for a in chunk:
                t = tmp[a]
                observations[a].append({
                    'endpoint': ep_name,
                    'code_sha256': code_sha(t.get('code')),
                    'code_bytes': (len(t.get('code','')) - 2) // 2 if isinstance(t.get('code'),str) and t.get('code','').startswith('0x') else None,
                    'token0': decode_address(t.get('token0')),
                    'token1': decode_address(t.get('token1')),
                    'factory': decode_address(t.get('factory')),
                    'has_reserves': isinstance(t.get('reserves'), str) and t.get('reserves','').startswith('0x') and len(t.get('reserves','')) >= 194,
                    'has_slot0': isinstance(t.get('slot0'), str) and t.get('slot0','') not in ('0x','0x0'),
                    'has_liquidity': decode_uint(t.get('liquidity')) is not None,
                    'fee': decode_uint(t.get('fee')),
                })
    for a in addresses:
        row = by_addr[a]
        obs = [x for x in observations[a] if x.get('code_sha256')]
        base_token = normalized((row.get('base_token') or {}).get('address'))
        quote_token = normalized((row.get('quote_token') or {}).get('address'))
        def matches(o):
            return {o.get('token0'), o.get('token1')} == {base_token, quote_token} if o.get('token0') and o.get('token1') else False
        binding_ok = [o for o in obs if matches(o)]
        code_set = {o.get('code_sha256') for o in obs}
        adapter = 'V3_CONCENTRATED_LIQUIDITY' if any(o.get('has_slot0') and o.get('has_liquidity') and o.get('fee') is not None for o in obs) else ('V2_CONSTANT_PRODUCT' if any(o.get('has_reserves') for o in obs) else 'UNKNOWN_EVM_PAIR')
        row['onchain_binding'] = {
            'status': 'VERIFIED_MULTI_RPC' if len(obs) >= 2 and len(code_set) == 1 and len(binding_ok) >= 2 else ('VERIFIED_SINGLE_RPC' if binding_ok else 'BLOCKED'),
            'adapter_family': adapter,
            'observations': obs,
            'token_binding_match': bool(binding_ok),
            'factory_addresses': sorted({o['factory'] for o in obs if o.get('factory')}),
        }
    return pairs

def main():
    tokens = load_jsonl(TOKEN_FILE); pairs = load_jsonl(PAIR_FILE)
    candidates = load_rpcs()
    probes = [x for x in map(probe_endpoint, candidates) if x['ok']]
    probes.sort(key=lambda x: [n for n,_ in candidates].index(x['name']))
    if len(probes) < MAX_ENDPOINTS:
        raise SystemExit(f'ONCHAIN_BINDING_NOT_ENOUGH_RPC_ENDPOINTS healthy={len(probes)} required={MAX_ENDPOINTS}')
    endpoints = [(x['name'], x['url']) for x in probes[:MAX_ENDPOINTS]]
    tokens = enrich_tokens(tokens, endpoints)
    pairs = enrich_pairs(pairs, endpoints)
    write_jsonl(TOKEN_FILE, tokens)
    write_jsonl(PAIR_FILE, pairs)
    pools = load_jsonl(POOL_FILE)
    pool_map = {normalized(x.get('pool_ref')): x for x in pools}
    for p in pairs:
        a = normalized(p.get('pair_address') or p.get('pairAddress'))
        if a in pool_map:
            b = p.get('onchain_binding') or {}
            pool_map[a].update({
                'adapter_family': b.get('adapter_family'),
                'onchain_binding_status': b.get('status'),
                'factory_addresses': b.get('factory_addresses', []),
                'token_binding_match': b.get('token_binding_match'),
            })
    write_jsonl(POOL_FILE, list(sorted(pool_map.values(), key=lambda x: normalized(x.get('pool_ref')))))
    d = json.loads(DEX_FILE.read_text())
    for rec in d.get('records', []):
        ns = normalized(rec.get('dex_namespace'))
        bound = [p for p in pairs if normalized(p.get('dex_namespace')) == ns]
        fac = sorted({f for p in bound for f in (p.get('onchain_binding') or {}).get('factory_addresses', [])})
        adapters = sorted({(p.get('onchain_binding') or {}).get('adapter_family') for p in bound if (p.get('onchain_binding') or {}).get('adapter_family')})
        verified = sum(1 for p in bound if (p.get('onchain_binding') or {}).get('status') in ('VERIFIED_MULTI_RPC','VERIFIED_SINGLE_RPC'))
        rec['factory_addresses'] = fac
        rec['adapter_families_observed'] = adapters
        rec['onchain_bound_pairs'] = verified
        rec['onchain_binding_status'] = 'VERIFIED_COMPLETE' if bound and verified == len(bound) else ('PARTIAL' if verified else 'BLOCKED')
    d['binding'] = {'rpc_endpoints': [x[0] for x in endpoints], 'observed_at': now(), 'requirement': 'read-only on-chain static identity; no signing'}
    DEX_FILE.write_text(json.dumps(d, indent=2, sort_keys=True) + '\n')
    token_multi = sum(1 for x in tokens if (x.get('onchain_identity') or {}).get('status') == 'VERIFIED_MULTI_RPC')
    pair_multi = sum(1 for x in pairs if (x.get('onchain_binding') or {}).get('status') == 'VERIFIED_MULTI_RPC')
    pair_ok = sum(1 for x in pairs if (x.get('onchain_binding') or {}).get('status') in ('VERIFIED_MULTI_RPC','VERIFIED_SINGLE_RPC'))
    result = {
        'schema': 'polygon-static-onchain-binding-v1', 'chain_id': 137, 'observed_at': now(),
        'rpc_endpoints': [x[0] for x in endpoints], 'rpc_blocks': {x['name']: x['block'] for x in probes[:MAX_ENDPOINTS]},
        'tokens': len(tokens), 'token_multi_rpc': token_multi, 'pairs': len(pairs), 'pair_multi_rpc': pair_multi, 'pair_bound': pair_ok,
        'pair_binding_complete': pair_ok == len(pairs),
        'pair_multi_rpc_complete': pair_multi == len(pairs),
        'status': 'GREEN' if pair_ok == len(pairs) and pair_multi == len(pairs) else 'OPEN',
    }
    (P / 'STATIC_ONCHAIN_BINDING.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    master_path = P / 'MASTER_INDEX.json'
    master = json.loads(master_path.read_text())
    master.setdefault('static_inputs', {})['onchain_binding'] = 'STATIC_ONCHAIN_BINDING.json'
    master['onchain_binding_status'] = result['status']
    master['onchain_binding_endpoints'] = [x[0] for x in endpoints]
    master_path.write_text(json.dumps(master, indent=2, sort_keys=True) + '\n')
    sat_path = P / 'STATIC_SATURATION_MANIFEST.json'
    sat = json.loads(sat_path.read_text())
    sat['onchain_binding'] = result
    sat['status'] = 'STATIC_MARKET_UNIVERSE_GREEN_WITH_MULTI_RPC_BINDING' if result['status'] == 'GREEN' else 'STATIC_MARKET_UNIVERSE_OPEN_ONCHAIN_BINDING'
    sat_path.write_text(json.dumps(sat, indent=2, sort_keys=True) + '\n')
    if result['status'] != 'GREEN':
        raise SystemExit('PAIR_ONCHAIN_BINDING_INCOMPLETE ' + json.dumps(result, sort_keys=True))
    print(json.dumps(result, sort_keys=True))

if __name__ == '__main__':
    main()
