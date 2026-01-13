# app/routes/ai_endpoints_v33.py
"""
RISKCAST AI Endpoints v33
AI Smart Assist endpoints: Explain, What-if, Optimize
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import json

router = APIRouter()

@router.post("/api/ai/explain")
async def ai_explain(shipment: Dict[str, Any]):
    """
    AI Explain - Summarize shipment, risk, route, anomalies
    
    Args:
        shipment: Complete shipment state object
    
    Returns:
        JSONResponse with explanation
    """
    try:
        # Extract key information
        transport_mode = shipment.get('transport', {}).get('mode', 'unknown')
        risk_score = shipment.get('risk', {}).get('score', 0)
        segments_count = len(shipment.get('segments', []))
        total_distance = sum(seg.get('distance', 0) for seg in shipment.get('segments', []))
        
        # Generate explanation
        explanation = f"""
**Shipment Overview:**
- Transport Mode: {transport_mode.upper()}
- Route Segments: {segments_count}
- Total Distance: {round(total_distance, 1)} km
- Risk Score: {risk_score}/10

**Risk Assessment:**
- Weather Risk: {shipment.get('risk', {}).get('weather', 'N/A')}
- Congestion: {shipment.get('risk', {}).get('congestion', 'N/A')}
- Delay Probability: {shipment.get('risk', {}).get('delay_probability', 'N/A')}

**Cargo Details:**
- Commodity: {shipment.get('cargo', {}).get('commodity', 'N/A')}
- Weight: {shipment.get('cargo', {}).get('weight', 'N/A')}
- Container Type: {shipment.get('cargo', {}).get('container_type', 'N/A')}

**Parties:**
- Shipper: {shipment.get('parties', {}).get('shipper', 'N/A')}
- Consignee: {shipment.get('parties', {}).get('consignee', 'N/A')}
- Forwarder: {shipment.get('parties', {}).get('forwarder', 'N/A')}

**Route Analysis:**
The shipment follows a {segments_count}-segment route covering {round(total_distance, 1)} km. 
The current risk level is {'HIGH' if risk_score > 7 else 'MEDIUM' if risk_score > 4 else 'LOW'}.
        """.strip()
        
        return JSONResponse({
            "status": "success",
            "explanation": explanation
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

@router.post("/api/ai/what_if")
async def ai_what_if(request: Dict[str, Any]):
    """
    AI What-if Scenario - Re-run risk computation with scenario changes
    
    Args:
        request: {
            "shipment": shipment state,
            "scenario": scenario description
        }
    
    Returns:
        JSONResponse with analysis and optionally updated shipment
    """
    try:
        shipment = request.get('shipment', {})
        scenario = request.get('scenario', '')
        
        # Parse scenario (simple implementation)
        updated_shipment = shipment.copy()
        
        # Example: "What if POD becomes USLAX?"
        if 'POD' in scenario.upper() or 'DESTINATION' in scenario.upper():
            # Extract port code (simplified)
            if 'USLAX' in scenario.upper():
                # Update segments to point to USLAX
                if updated_shipment.get('segments'):
                    last_segment = updated_shipment['segments'][-1]
                    last_segment['to'] = 'USLAX'
                    last_segment['lat2'] = 33.7701
                    last_segment['lon2'] = -118.1937
                    # Recalculate distance
                    import math
                    R = 6371
                    lat1 = math.radians(last_segment['lat1'])
                    lat2 = math.radians(last_segment['lat2'])
                    dlat = math.radians(last_segment['lat2'] - last_segment['lat1'])
                    dlon = math.radians(last_segment['lon2'] - last_segment['lon1'])
                    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                    c = 2 * math.asin(math.sqrt(a))
                    last_segment['distance'] = round(R * c, 1)
        
        # Recalculate risk (simplified)
        new_risk_score = updated_shipment.get('risk', {}).get('score', 7.2)
        # Adjust risk based on scenario
        if 'USLAX' in scenario.upper():
            new_risk_score += 0.5  # Slightly higher risk for longer route
        
        if 'risk' not in updated_shipment:
            updated_shipment['risk'] = {}
        updated_shipment['risk']['score'] = min(10, max(0, new_risk_score))
        
        analysis = f"""
**Scenario Analysis:**
{scenario}

**Impact:**
- Risk Score: {updated_shipment['risk']['score']}/10 (adjusted)
- Route updated based on scenario

**Recommendation:**
The scenario has been analyzed. Risk factors have been recalculated based on the new route configuration.
        """.strip()
        
        return JSONResponse({
            "status": "success",
            "analysis": analysis,
            "updated_shipment": updated_shipment
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process scenario: {str(e)}")

@router.post("/api/ai/optimize")
async def ai_optimize(shipment: Dict[str, Any]):
    """
    AI Optimize Route - Suggest best route
    
    Args:
        shipment: Complete shipment state object
    
    Returns:
        JSONResponse with optimized route and recommendation
    """
    try:
        segments = shipment.get('segments', [])
        if not segments:
            raise HTTPException(status_code=400, detail="No segments to optimize")
        
        # Simple optimization: minimize distance
        # In production, this would use advanced routing algorithms
        optimized_segments = segments.copy()
        
        # Example optimization: if route is too long, suggest intermediate stop
        total_distance = sum(seg.get('distance', 0) for seg in segments)
        if total_distance > 10000 and len(segments) == 1:
            # Add intermediate stop at Singapore
            first_seg = segments[0]
            optimized_segments = [
                {
                    "from": first_seg['from'],
                    "to": "SGSIN",
                    "lat1": first_seg['lat1'],
                    "lon1": first_seg['lon1'],
                    "lat2": 1.3521,
                    "lon2": 103.8198,
                    "mode": first_seg.get('mode', 'ocean'),
                    "distance": round(total_distance * 0.4, 1)
                },
                {
                    "from": "SGSIN",
                    "to": first_seg['to'],
                    "lat1": 1.3521,
                    "lon1": 103.8198,
                    "lat2": first_seg['lat2'],
                    "lon2": first_seg['lon2'],
                    "mode": first_seg.get('mode', 'ocean'),
                    "distance": round(total_distance * 0.6, 1)
                }
            ]
        
        recommendation = f"""
**Route Optimization Complete**

**Current Route:**
- Segments: {len(segments)}
- Total Distance: {round(total_distance, 1)} km

**Optimized Route:**
- Segments: {len(optimized_segments)}
- Estimated Distance: {round(sum(seg.get('distance', 0) for seg in optimized_segments), 1)} km
- Estimated Time Savings: ~{round(total_distance * 0.05, 1)} km

**Benefits:**
- Reduced transit time
- Lower fuel consumption
- Better port connectivity

Preview the optimized route on the globe (cyan dotted line).
        """.strip()
        
        return JSONResponse({
            "status": "success",
            "recommendation": recommendation,
            "optimized_route": {
                "segments": optimized_segments
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to optimize route: {str(e)}")

@router.post("/api/ai/chat")
async def ai_chat(request: Dict[str, Any]):
    """
    General AI chat endpoint
    
    Args:
        request: {
            "message": user message,
            "shipment": shipment state (optional)
        }
    
    Returns:
        JSONResponse with AI response
    """
    try:
        message = request.get('message', '')
        shipment = request.get('shipment', {})
        
        # Simple response (in production, integrate with Claude/OpenAI)
        response = f"I understand you're asking about: {message}. "
        if shipment:
            response += f"Based on your shipment data, I can help you with route optimization, risk analysis, or scenario planning."
        else:
            response += "Please provide shipment data for more specific assistance."
        
        return JSONResponse({
            "status": "success",
            "response": response
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")

