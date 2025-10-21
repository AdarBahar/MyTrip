# AI Route Optimization API

This document describes the new AI-powered route optimization endpoint that integrates with OpenAI's GPT models to provide intelligent route suggestions using natural language instructions.

## Overview

The AI route optimization endpoint allows users to:
- Optimize route order using natural language prompts
- Handle complex routing constraints with flexible instructions
- Get human-readable route analysis and suggestions
- Support both structured and unstructured data inputs

## Endpoint Details

### POST `/ai/route-optimize`

**Authentication Required:** Bearer token

**Request Body:**
```json
{
  "prompt": "string (required, 1-2000 chars)",
  "data": "string or object (required)",
  "response_structure": "string (required, 1-1000 chars)"
}
```

**Response:**
```json
{
  "result": "string",
  "raw_response": "object (optional, debug mode only)",
  "metadata": {
    "model": "string",
    "tokens_used": {
      "prompt_tokens": "number",
      "completion_tokens": "number",
      "total_tokens": "number"
    },
    "finish_reason": "string"
  }
}
```

## Configuration

### Environment Variables

Add to your `.env` or production environment:

```bash
# AI Configuration
OPENAI_API_KEY=your-openai-api-key-here
```

### Installation

The OpenAI Python SDK is required:

```bash
pip install openai==1.3.7
```

## Usage Examples

### Basic Route Optimization

```json
{
  "prompt": "Create the right order of the route, assuming that start and end are book-endings, and stops are ordered in the optimized route.",
  "data": "Type | Location | Address\nStart | 32.1878296, 34.9354013 | מיכל, כפר סבא, ישראל\nEnd | 32.067444, 34.7936703 | יגאל אלון, תל־אביב–יפו, ישראל\nStop | 32.1962854, 34.8766859 | רננים, רעננה, ישראל\nStop | 32.1739447, 34.8081801 | הרצליה פיתוח, הרצליה, ישראל",
  "response_structure": "Start: Location (coordinates)\nStop 1: Location (coordinates)\nStop 2: Location (coordinates)\nEnd: Location (coordinates)"
}
```

### Fixed Constraints

```json
{
  "prompt": "Optimize the route but keep the second stop fixed in its current position. The other stops can be reordered for efficiency.",
  "data": "Start: Jerusalem\nStop 1: Bethlehem\nStop 2: Hebron (FIXED)\nStop 3: Beersheba\nEnd: Eilat",
  "response_structure": "1. Start location\n2. Stop location\n3. Stop location\n4. End location"
}
```

### Structured Data Input

```json
{
  "prompt": "Optimize this route for shortest travel time",
  "data": {
    "stops": [
      {"name": "Start", "lat": 32.1878296, "lon": 34.9354013, "address": "Kfar Saba"},
      {"name": "Stop 1", "lat": 32.1962854, "lon": 34.8766859, "address": "Raanana"},
      {"name": "Stop 2", "lat": 32.1739447, "lon": 34.8081801, "address": "Herzliya"}
    ]
  },
  "response_structure": "Optimized order: Stop name (address)"
}
```

## Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Authentication required"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "prompt"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Configuration Error:**
```json
{
  "detail": "AI service not configured. Please contact support."
}
```

**429 Rate Limit:**
```json
{
  "detail": "AI service temporarily unavailable due to high demand. Please try again in a few moments."
}
```

## Health Check

### GET `/ai/health`

Check if the AI service is properly configured:

```json
{
  "status": "healthy",
  "service": "ai-route-optimization",
  "openai_configured": true,
  "endpoints": ["/ai/route-optimize"]
}
```

## Best Practices

### Prompt Engineering

1. **Be Specific:** Clearly state your optimization criteria
   - ✅ "Optimize for shortest travel time"
   - ❌ "Make it better"

2. **Mention Constraints:** Explicitly state any fixed requirements
   - ✅ "Keep the lunch stop at 12:00 PM fixed"
   - ✅ "Start and end points cannot change"

3. **Provide Context:** Include relevant information about the route
   - ✅ "This is a tourist route prioritizing scenic views"
   - ✅ "Business trip requiring efficient travel between meetings"

### Data Formatting

1. **Consistent Structure:** Use consistent formatting for location data
2. **Include Addresses:** Provide human-readable addresses when possible
3. **Mark Fixed Points:** Clearly indicate any stops that cannot be moved

### Response Structure

1. **Clear Format:** Specify exactly how you want the response formatted
2. **Include Details:** Request coordinates, addresses, or other needed info
3. **Numbering:** Use clear numbering or ordering in your template

## Integration Examples

### cURL Example

```bash
curl -X POST "https://your-api.com/ai/route-optimize" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Optimize this route for a family trip with kids",
    "data": "Start: Tel Aviv\nStop: Safari Park\nStop: Beach\nEnd: Hotel",
    "response_structure": "1. Location - reason for placement"
  }'
```

### Python Example

```python
import requests

response = requests.post(
    "https://your-api.com/ai/route-optimize",
    headers={"Authorization": "Bearer your-token"},
    json={
        "prompt": "Create efficient route for business meetings",
        "data": route_data,
        "response_structure": "Meeting 1: Location\nMeeting 2: Location"
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Optimized route: {result['result']}")
    print(f"Tokens used: {result['metadata']['tokens_used']['total_tokens']}")
```

## Limitations

1. **API Costs:** Each request consumes OpenAI API tokens
2. **Rate Limits:** Subject to OpenAI's rate limiting policies
3. **Response Quality:** Depends on prompt clarity and data quality
4. **No Real-time Traffic:** AI suggestions don't include live traffic data

## Troubleshooting

### Common Issues

1. **"AI service not configured"**
   - Check OPENAI_API_KEY environment variable
   - Verify API key is valid

2. **"AI service dependencies not available"**
   - Install OpenAI package: `pip install openai`
   - Check requirements.txt includes openai

3. **Authentication errors**
   - Verify your API token is valid
   - Check token hasn't expired

4. **Rate limit errors**
   - Wait before retrying
   - Consider implementing exponential backoff

### Testing

Use the provided test script:

```bash
python tools/test_ai_route_optimization.py
```

## Security Considerations

1. **API Key Protection:** Never expose OpenAI API keys in client-side code
2. **Input Validation:** All inputs are validated before sending to OpenAI
3. **Rate Limiting:** Consider implementing additional rate limiting for cost control
4. **Logging:** API calls are logged for monitoring and debugging

## Future Enhancements

Potential improvements for future versions:

1. **Caching:** Cache similar requests to reduce API costs
2. **Integration:** Direct integration with existing route computation
3. **Templates:** Pre-built prompt templates for common use cases
4. **Validation:** Parse and validate AI responses against route data
5. **Multi-language:** Support for multiple languages in prompts
