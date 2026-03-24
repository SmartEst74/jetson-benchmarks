# Code Reviewer — Benchmark Prompts

**Purpose**: Test a model's ability to find bugs, security issues, and suggest improvements in existing code.

**Scoring**: Each prompt is graded on correctness (30%), completeness (25%), code quality (20%), robustness (15%), documentation (10%).

---

## Prompt CR-1: Vulnerable Flask Endpoint (Complexity: ★★★★☆)

**Tests**: Security analysis, SQL injection detection, JWT issues

```
Review this Python endpoint for ALL issues. Use priority markers (blocker/suggestion/nit):

@app.route('/api/query', methods=['POST'])
def query():
    data = request.json
    sql = f"SELECT * FROM users WHERE name = '{data['name']}' AND role = '{data['role']}'"
    result = db.execute(sql)
    token = jwt.encode({'user': data['name']}, 'secret123', algorithm='HS256')
    response = make_response(jsonify({'data': result.fetchall(), 'token': token}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
```

**Expected**: Find SQL injection, hardcoded JWT secret, missing input validation, CORS wildcard, missing error handling.

---

## Prompt CR-2: Race Condition in Counter (Complexity: ★★★☆☆)

**Tests**: Concurrency issues, atomic operations, testing

```
Review this async counter implementation for race conditions:

```python
class Counter:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.key = "counter:total"
    
    async def increment(self, amount=1):
        current = await self.redis.get(self.key)
        new_value = int(current or 0) + amount
        await self.redis.set(self.key, new_value)
        return new_value
    
    async def get(self):
        return int(await self.redis.get(self.key) or 0)
```

Identify the race condition and provide the fixed version.
```

**Expected**: Identify GET-then-SET race condition, suggest INCR or WATCH/MULTI/EXEC.

---

## Prompt CR-3: Memory Leak in React Component (Complexity: ★★★★★)

**Tests**: React lifecycle, cleanup, memory management

```
Review this React component for memory leaks and performance issues:

```tsx
function DataStream({ url }: { url: string }) {
  const [data, setData] = useState<any[]>([]);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    ws.onmessage = (event) => {
      setData(prev => [...prev, JSON.parse(event.data)]);
    };
    
    fetch(url.replace('ws:', 'http:'))
      .then(r => r.json())
      .then(history => setData(history));
    
    const interval = setInterval(() => {
      console.log('Data count:', data.length);
    }, 1000);
  }, [url]);
  
  return (
    <div>
      {data.map((item, i) => (
        <div key={i}>{JSON.stringify(item)}</div>
      ))}
    </div>
  );
}
```

Identify all issues and provide the fixed version.
```

**Expected**: Missing WebSocket close, missing clearInterval, stale closure in setInterval, index as key, missing error handling.
