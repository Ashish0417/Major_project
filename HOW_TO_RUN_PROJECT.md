# How to Run the Travel Planner Project

To get your Travel Planner application up and running, you will need to start three separate components: the MongoDB database, the FastAPI backend, and the Next.js frontend. 

It is recommended to open **three separate terminal windows** (or tabs) to run these services simultaneously.

---

## 🟢 Terminal 1: Start MongoDB (Database)

First, make sure **Docker Desktop** is open and running on your system.

**1. Check if the container is already created and just stopped:**
```bash
docker start mongodb
```
*If this command works and returns `mongodb`, your database is running and you can move to Terminal 2!*

**2. If the container does not exist yet (Error: No such container: mongodb), run this command to create and start it:**
```bash
docker run -d --name mongodb -p 27017:27017 -v mongodb_data:/data/db mongo
```

> **Optional Tip:** If you ever need to view your data directly inside MongoDB, you can use:
> ```bash
> docker exec -it mongodb mongosh
> use travel_planner
> db.getCollectionNames().forEach(function(collName) {
>   print("\n--- Collection: " + collName + " ---");
>   db[collName].find().forEach(printjson);
> });
> ```

---

## 🔵 Terminal 2: Start the FastAPI Backend

Keep Terminal 1 running and open a **second terminal**. Ensure you are inside your `Major_project` directory (`c:\Users\tanvi\Personal\TravelPlanner\Major_project`) and your virtual environment is activated.

**1. Run the FastAPI application:**
```bash
python fastapi_app.py
```
*(Alternatively, you can run `uvicorn fastapi_app:app --reload`)*

The backend should now be running locally on port 8000.

---

## 🟠 Terminal 3: Start the Next.js Frontend

Open a **third terminal** for the frontend UI. 

**1. Ensure pnpm is installed globally (using npm):**
```bash
npm install -g pnpm
```

**2. Install the necessary markdown dependencies (if not already installed):**
```bash
pnpm add -D remark-gfm react-markdown
```

**3. Navigate to the Frontend directory:**
```bash
cd Frontend
```

**4. Install any remaining frontend dependencies and start the development server:**
```bash
pnpm install
pnpm dev
```

---

### 🎉 All Done!

Once all three terminals are active and show no errors, you can open your browser to **http://localhost:3000** to use the Travel Planner project.
