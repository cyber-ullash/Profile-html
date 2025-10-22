from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse 
import httpx

# আপনার মূল Node.js সার্ভারের ঠিকানা
UPSTREAM_API = "http://2.56.246.81:30165"  

# FastAPI ইনিশিয়ালাইজেশন: docs_url এবং redoc_url দুটিকেই None সেট করে বন্ধ করা হলো
# এটি FastAPI-এর ডিফল্ট ডকুমেন্টেশন তৈরি করা বন্ধ করে দেয়।
app = FastAPI(docs_url=None, redoc_url=None) 

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    async with httpx.AsyncClient() as client:
        try:
            upstream_response = await client.get(
                f"{UPSTREAM_API}/",
                timeout=20.0
            )
            
            upstream_response.raise_for_status()

            return HTMLResponse(
                content=upstream_response.content.decode('utf-8'),
                status_code=upstream_response.status_code
            )
        except httpx.RequestError as e:
            return Response(
                content=f"Error fetching homepage from upstream: {e}",
                status_code=500
            )

# বাকি সমস্ত রিকোয়েস্টকে প্রক্সি করা, যার মধ্যে এখন /docs রিকোয়েস্টও Node.js এর কাছে যাবে।
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def mask_api(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        upstream_url = f"{UPSTREAM_API}/{path}"
        
        # Accept-Encoding header বাদ দেওয়া হলো 
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "user-agent", "accept-encoding"]}
        method = request.method
        params = dict(request.query_params)
        data = await request.body()

        upstream_response = await client.request(
            method,
            upstream_url,
            headers=headers,
            params=params,
            content=data,
            timeout=20.0
        )

        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type")
        )
