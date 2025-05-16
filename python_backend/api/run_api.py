import uvicorn

if __name__ == "__main__":
    print("Starting UNOPS Remote Sensing API server...")
    uvicorn.run("projects_api:app", host="0.0.0.0", port=8000, reload=True)
