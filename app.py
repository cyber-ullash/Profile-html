from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI()

# আপনার মূল Node.js সার্ভারের ঠিকানা
UPSTREAM_API = "http://2.56.246.81:30165"  

# 1. মূল HTML ফাইল পরিবেশনের জন্য রুট সংজ্ঞায়িত করা
# এই রুটটি নিশ্চিত করবে যে ব্রাউজারে portal.html ফাইলটি লোড হচ্ছে
@app.get("/")
async def get_homepage():
    async with httpx.AsyncClient() as client:
        try:
            # Node.js সার্ভার থেকে সরাসরি portal.html কন্টেন্ট আনো
            upstream_response = await client.get(
                f"{UPSTREAM_API}/",
                timeout=20.0
            )
            
            # HTML কন্টেন্টকে Render আউটপুটে সরাসরি রিটার্ন করো
            return Response(
                content=upstream_response.content,
                status_code=upstream_response.status_code,
                media_type=upstream_response.headers.get("content-type", "text/html")
            )
        except httpx.RequestError as e:
            return Response(
                content=f"Error fetching homepage from upstream: {e}",
                status_code=500
            )

# 2. বাকি সমস্ত API রিকোয়েস্টকে প্রক্সি করা
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def mask_api(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        upstream_url = f"{UPSTREAM_API}/{path}"
        
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
