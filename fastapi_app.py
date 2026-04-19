# import os
# from fastapi import FastAPI, HTTPException, Depends, Request
# from fastapi.responses import HTMLResponse
# from pydantic import BaseModel, EmailStr
# from typing import List, Optional
# import jwt
# from passlib.context import CryptContext
# from datetime import datetime, timedelta

# from llm_orchestrator import TravelItineraryOrchestrator
# from user_profile import UserProfile, TravelPreferences, TripDates, ContactInfo

# app = FastAPI(title="Travel Planner API")
# orchestrator = TravelItineraryOrchestrator()
# history_manager = orchestrator.history_manager

# # --- Auth Config ---
# SECRET_KEY = "your-super-secret-key-for-travel-app"
# ALGORITHM = "HS256"
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # --- Pydantic Models ---
# class SignupRequest(BaseModel):
#     name: str
#     email: EmailStr
#     phone: str
#     password: str
#     travel_theme: str
#     budget_tier: str

# class LoginRequest(BaseModel):
#     email: EmailStr
#     password: str

# class ChatRequest(BaseModel):
#     query: str

# class FeedbackRequest(BaseModel):
#     query: str
#     rating: int
#     comment: str = ""

# # --- Utils ---
# def get_password_hash(password: str) -> str:
#     return pwd_context.hash(password)

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)

# def create_access_token(data: dict):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(days=7)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# def get_current_user_id(request: Request):
#     auth_header = request.headers.get("Authorization")
#     if not auth_header or not auth_header.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Missing or invalid token")
#     token = auth_header.split(" ")[1]
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("sub")
#         if user_id is None:
#             raise HTTPException(status_code=401, detail="Invalid token payload")
#         return user_id
#     except jwt.PyJWTError:
#         raise HTTPException(status_code=401, detail="Token verification failed")

# # --- Endpoints ---

# @app.post("/auth/signup")
# def signup(req: SignupRequest):
#     email_str = str(req.email)
#     users = []
#     if history_manager.use_mongodb:
#         users = list(history_manager.collection.find({"contact.email": email_str}))
#     else:
#         users = [u for u in history_manager.memory_storage['users'].values() if u.get('contact', {}).get('email') == email_str]
    
#     if len(users) > 0:
#         raise HTTPException(status_code=400, detail="Email already registered")

#     # Calculate weights based on generic preferences
#     w_cost, w_time, w_pref, w_pop = 0.3, 0.2, 0.3, 0.2
    
#     if req.travel_theme == 'nature':
#         w_pref, w_pop = 0.4, 0.1
#     elif req.travel_theme == 'adventure':
#         w_time, w_pref = 0.1, 0.4
#     elif req.travel_theme == 'historical':
#         w_pref = 0.5
#     elif req.travel_theme == 'relaxing':
#         w_time, w_pref, w_cost = 0.4, 0.3, 0.2
        
#     comfort = "economy"
#     if req.budget_tier == 'budget':
#         w_cost, w_pref = 0.5, 0.2
#     elif req.budget_tier == 'luxury':
#         w_cost, w_pref, comfort = 0.1, 0.5, "luxury"
#     else:
#         comfort = "premium"

#     profile = UserProfile()
#     profile.name = req.name
#     profile.contact = ContactInfo(email=email_str, phone=req.phone)
#     profile.travel_preferences = TravelPreferences(
#         comfort_level=comfort,
#         activity_interests=[req.travel_theme],
#         weight_cost=w_cost,
#         weight_time=w_time,
#         weight_preference=w_pref,
#         weight_popularity=w_pop
#     )
    
#     # Store profile normally
#     history_manager.store_user_profile(profile)
    
#     # We also need to store the password hash. Since `store_user_profile` overwrites with `profile.to_dict()`,
#     # we'll inject the password manually after storing, or directly update the collection if using Mongo.
#     hashed_password = get_password_hash(req.password)
    
#     if history_manager.use_mongodb:
#         history_manager.collection.update_one(
#             {'user_id': profile.user_id},
#             {'$set': {'password_hash': hashed_password}}
#         )
#     else:
#         history_manager.memory_storage['users'][profile.user_id]['password_hash'] = hashed_password

#     # Generate token
#     token = create_access_token({"sub": profile.user_id})
#     return {"message": "Signup successful", "access_token": token, "user_id": profile.user_id}

# @app.post("/auth/login")
# def login(req: LoginRequest):
#     user_doc = None
#     email_str = str(req.email)
#     if history_manager.use_mongodb:
#         user_doc = history_manager.collection.find_one({"contact.email": email_str})
#     else:
#         for u in history_manager.memory_storage['users'].values():
#             if u.get('contact', {}).get('email') == email_str:
#                 user_doc = u
#                 break
                
#     if not user_doc or 'password_hash' not in user_doc:
#         raise HTTPException(status_code=401, detail="Invalid email or password")
        
#     if not verify_password(req.password, user_doc['password_hash']):
#         raise HTTPException(status_code=401, detail="Invalid email or password")
        
#     token = create_access_token({"sub": user_doc['user_id']})
#     return {"message": "Login successful", "access_token": token, "user_id": user_doc['user_id']}

# from fastapi.responses import StreamingResponse

# @app.post("/api/chat")
# async def chat_endpoint(req: ChatRequest, user_id: str = Depends(get_current_user_id)):
#     if not req.query:
#         raise HTTPException(status_code=400, detail="Empty query")
#     try:
#         return StreamingResponse(
#             orchestrator.ask_stream(req.query, user_id=user_id), 
#             media_type="text/event-stream"
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/feedback")
# def feedback_endpoint(req: FeedbackRequest, user_id: str = Depends(get_current_user_id)):
#     if req.rating not in (0, 1):
#         raise HTTPException(status_code=400, detail="Rating must be 0 or 1")
#     history_manager.store_feedback(user_id, req.query, req.rating, req.comment)
#     return {"status": "Feedback stored successfully"}

# # --- Frontend HTML ---
# HTML_TEMPLATE = """
# <!doctype html>
# <html lang="en">
# <head>
#   <meta charset="utf-8" />
#   <meta name="viewport" content="width=device-width, initial-scale=1" />
#   <title>Travel Planner FastAPI</title>
#   <style>
#     body { font-family: Arial, sans-serif; background: #f4f7fb; margin:0; padding:0; display:flex; justify-content:center; align-items:center; min-height:100vh;}
#     .container { width: 100%; max-width: 800px; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin:20px; }
#     h1 {text-align:center;}
    
#     /* Pages */
#     .page { display: none; }
#     .page.active { display: block; }
    
#     /* Forms */
#     .form-group { margin-bottom: 15px; }
#     .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
#     .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;}
#     button.btn { padding: 10px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; width: 100%; font-size:16px;}
#     button.btn:hover { background: #0056b3; }
#     .error { color: red; margin-top:10px; text-align:center;}
#     .link { color: #007bff; cursor:pointer; text-decoration:underline; text-align:center; display:block; margin-top:10px; }
    
#     /* Chat */
#     .messages { min-height: 400px; max-height: 500px; border: 1px solid #ddd; padding: 12px; border-radius: 6px; background: #fff; overflow-y: auto; display: flex; flex-direction: column; margin-bottom: 15px;}
#     .bubble { margin: 10px 0; padding: 10px 12px; border-radius: 12px; display: inline-block; max-width: 80%; line-height: 1.4; word-wrap:break-word;}
#     .user { background: #dbe8ff; align-self: flex-end; }
#     .bot { background: #e8f7e4; align-self: flex-start; }
#     .typing { font-style: italic; color: #999; }
#     .row { display: flex; align-items: center; gap: 10px; }
#     #queryInput { flex:1; padding: 10px; border: 1px solid #ccc; border-radius: 6px; }
#     #sendBtn { padding: 10px 20px; }
    
#     /* Advanced Feedback */
#     .feedback-box { display: flex; flex-direction: column; gap:10px; background: #f9f9f9; border: 1px solid #eee; padding:10px; border-radius:6px; margin-top:15px; }
#     .feedback-row { display: flex; gap: 5px; align-items: center;}
#     .feedback-row button { border: 1px solid #ccc; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size:16px;}
#     .feedback-row button.up { background-color: #c6f6d5; }
#     .feedback-row button.down { background-color: #fed7d7; }
#     #feedbackComment { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
#   </style>
# </head>
# <body>
  
#   <div class="container">
#     <h1>Travel Planner</h1>
#     <div id="errorBox" class="error"></div>
    
#     <!-- LOGIN PAGE -->
#     <div id="loginPage" class="page active">
#       <h2>Provide Credentials</h2>
#       <div class="form-group">
#         <label>Email</label>
#         <input type="email" id="loginEmail" placeholder="user@example.com" value="user@example.com" />
#       </div>
#       <div class="form-group">
#         <label>Password</label>
#         <input type="password" id="loginPassword" placeholder="password" value="password123"/>
#       </div>
#       <button class="btn" onclick="login()">Login</button>
#       <span class="link" onclick="switchPage('signupPage')">New user? Create an account</span>
#     </div>

#     <!-- SIGNUP PAGE -->
#     <div id="signupPage" class="page">
#       <h2>Create Profile</h2>
#       <div class="form-group"><label>Name</label><input type="text" id="suName" value="Lasya Reddy"/></div>
#       <div class="form-group"><label>Email</label><input type="email" id="suEmail" value="user@example.com"/></div>
#       <div class="form-group"><label>Phone</label><input type="text" id="suPhone" value="+91-XXXXXXXXXX"/></div>
#       <div class="form-group"><label>Password</label><input type="password" id="suPassword" value="password123"/></div>
#       <div class="form-group"><label>Travel Theme</label>
#         <select id="suTheme">
#           <option value="nature">Nature & Wildlife</option>
#           <option value="adventure">Adventure</option>
#           <option value="historical">Historical & Cultural</option>
#           <option value="city">City & Urban</option>
#           <option value="relaxing">Relaxing</option>
#         </select>
#       </div>
#       <div class="form-group"><label>Budget Style</label>
#         <select id="suBudget">
#           <option value="budget">Budget Friendly</option>
#           <option value="moderate" selected>Moderate</option>
#           <option value="luxury">Luxury</option>
#         </select>
#       </div>
#       <button class="btn" onclick="signup()">Sign Up</button>
#       <span class="link" onclick="switchPage('loginPage')">Already have an account? Login</span>
#     </div>

#     <!-- CHAT PAGE -->
#     <div id="chatPage" class="page">
#       <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
#         <h2>Agent Chat</h2>
#         <button class="btn" style="width:auto; padding:5px 10px; background:#dc3545;" onclick="logout()">Logout</button>
#       </div>
      
#       <div class="messages" id="messages"></div>

#       <div class="row">
#         <input id="queryInput" placeholder="Ask me to plan your trip..." />
#         <button class="btn" id="sendBtn" style="width: auto;" onclick="sendMessage()">Send</button>
#       </div>

#       <!-- Advanced Feedback Section -->
#       <div class="feedback-box">
#         <strong>Feedback for last response:</strong>
#         <div class="feedback-row">
#           <button class="up" onclick="sendFeedback(1)">👍</button>
#           <button class="down" onclick="sendFeedback(0)">👎</button>
#           <input type="text" id="feedbackComment" placeholder="Add textual comments here before clicking rating..." />
#         </div>
#         <div id="status" style="font-size:14px; color: #666; margin-top:5px;"></div>
#       </div>
#     </div>
    
#   </div>

#   <script>
#     let token = localStorage.getItem("token");
#     let lastQuery = '';
    
#     if(token) switchPage('chatPage');

#     function switchPage(pageId) {
#       try {
#         document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
#         const target = document.getElementById(pageId);
#         if (target) target.classList.add('active');
        
#         const errBox = document.getElementById('errorBox');
#         if (errBox) errBox.innerText = '';
        
#         const statBox = document.getElementById('status');
#         if (statBox) statBox.innerText = '';
#       } catch(e) {
#         console.error(e);
#         alert("UI Error: " + e.message);
#       }
#     }

#     function logout() {
#       localStorage.removeItem("token");
#       token = null;
#       switchPage('loginPage');
#     }

#     async function apiCall(endpoint, payload, useAuth = false) {
#       const headers = { 'Content-Type': 'application/json' };
#       if (useAuth && token) headers['Authorization'] = 'Bearer ' + token;
      
#       const res = await fetch(endpoint, { method: 'POST', headers, body: JSON.stringify(payload) });
#       const data = await res.json();
#       if (!res.ok) {
#         if(res.status === 401) logout();
#         throw new Error(data.detail || 'API Error');
#       }
#       return data;
#     }

#     async function login() {
#       try {
#         const payload = {
#           email: document.getElementById('loginEmail').value,
#           password: document.getElementById('loginPassword').value
#         };
#         const data = await apiCall('/auth/login', payload);
#         token = data.access_token;
#         localStorage.setItem("token", token);
#         switchPage('chatPage');
#       } catch(e) {
#         document.getElementById('errorBox').innerText = e.message;
#         alert("Login Error: " + e.message);
#       }
#     }

#     async function signup() {
#       try {
#         const payload = {
#           name: document.getElementById('suName').value,
#           email: document.getElementById('suEmail').value,
#           phone: document.getElementById('suPhone').value,
#           password: document.getElementById('suPassword').value,
#           travel_theme: document.getElementById('suTheme').value,
#           budget_tier: document.getElementById('suBudget').value
#         };
#         const data = await apiCall('/auth/signup', payload);
#         token = data.access_token;
#         localStorage.setItem("token", token);
#         switchPage('chatPage');
#       } catch(e) {
#         document.getElementById('errorBox').innerText = e.message;
#         alert("Signup Error: " + e.message);
#       }
#     }

#     // --- Chat Logic ---
#     const messagesEl = document.getElementById('messages');
#     let typingBubble = null;

#     function addBubble(text, user) {
#       const div = document.createElement('div');
#       div.className = 'bubble ' + (user ? 'user' : 'bot');
#       div.innerHTML = text.replace(/\\n/g, '<br/>');
#       messagesEl.appendChild(div);
#       messagesEl.scrollTop = messagesEl.scrollHeight;
#     }

#     async function sendMessage() {
#       const inputEl = document.getElementById('queryInput');
#       const query = inputEl.value.trim();
#       if (!query) return;

#       addBubble(query, true);
#       lastQuery = query;
#       inputEl.value = '';
      
#       const typing = document.createElement('div');
#       typing.className = 'bubble bot typing';
#       typing.innerText = '✍️ Agent is thinking...';
#       messagesEl.appendChild(typing);
#       messagesEl.scrollTop = messagesEl.scrollHeight;

#       try {
#         const headers = { 'Content-Type': 'application/json' };
#         if (token) headers['Authorization'] = 'Bearer ' + token;
        
#         const res = await fetch('/api/chat', { 
#             method: 'POST', 
#             headers: headers,
#             body: JSON.stringify({ query: query })
#         });
        
#         if (!res.ok) {
#             if(res.status === 401) logout();
#             throw new Error('API Error: ' + res.status);
#         }
        
#         typing.remove();
        
#         const reader = res.body.getReader();
#         const decoder = new TextDecoder("utf-8");
#         let resultText = '';
        
#         const div = document.createElement('div');
#         div.className = 'bubble bot';
#         messagesEl.appendChild(div);
        
#         while (true) {
#             const { done, value } = await reader.read();
#             if (done) break;
#             resultText += decoder.decode(value, { stream: true });
            
#             let formatted = resultText.replace(/\\n/g, '<br/>');
#             formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
#             div.innerHTML = formatted;
#             messagesEl.scrollTop = messagesEl.scrollHeight;
#         }
        
#         document.getElementById('status').innerText = '✅ Ready for feedback.';
#       } catch(e) {
#         typing.remove();
#         addBubble('Error: ' + e.message, false);
#       }
#     }

#     document.getElementById('queryInput').addEventListener('keypress', (e) => { 
#       if (e.key === 'Enter') sendMessage(); 
#     });

#     async function sendFeedback(rating) {
#       if (!lastQuery) {
#         document.getElementById('status').innerText = '❌ Send a query first.';
#         return;
#       }
#       const commentInput = document.getElementById('feedbackComment');
#       const comment = commentInput.value.trim();
      
#       try {
#         const payload = { query: lastQuery, rating, comment };
#         await apiCall('/api/feedback', payload, true);
#         document.getElementById('status').innerText = '✅ Feedback saved successfully!';
#         commentInput.value = ''; // clear 
#       } catch(e) {
#         document.getElementById('status').innerText = '❌ Error saving feedback.';
#       }
#     }
#   </script>
# </body>
# </html>
# """

# @app.get("/", response_class=HTMLResponse)
# def index():
#     return HTML_TEMPLATE

# if __name__ == "__main__":
#     import uvicorn
#     # Make sure we use port 8000 so the user knows where it is
#     uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=True)
import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

from llm_orchestrator import TravelItineraryOrchestrator
from user_profile import UserProfile, TravelPreferences, ContactInfo
from feedback_predictor import predictor

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Travel Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
orchestrator = TravelItineraryOrchestrator()
history_manager = orchestrator.history_manager

# ================= AUTH =================
SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ================= MODELS =================
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    travel_theme: str
    budget_tier: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChatRequest(BaseModel):
    query: str

class SelectItineraryRequest(BaseModel):
    index: int

class ModelFeedbackRequest(BaseModel):
    user_id: str
    trip_id: str
    feedback: str

# ================= UTILS =================
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(p, h):
    return pwd_context.verify(p, h)

def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user_id(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    
    token = auth.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        raise HTTPException(401, "Invalid token")

# ================= SIGNUP =================
@app.post("/auth/signup")
def signup(req: SignupRequest):
    email = str(req.email)

    if history_manager.use_mongodb:
        existing = history_manager.collection.find_one({"contact.email": email})
    else:
        existing = next(
            (u for u in history_manager.memory_storage['users'].values()
             if u.get('contact', {}).get('email') == email),
            None
        )

    if existing:
        raise HTTPException(400, "Email already exists")

    profile = UserProfile()
    profile.name = req.name
    profile.contact = ContactInfo(email=email, phone=req.phone)

    history_manager.store_user_profile(profile)

    hashed = get_password_hash(req.password)

    if history_manager.use_mongodb:
        history_manager.collection.update_one(
            {"user_id": profile.user_id},
            {"$set": {"password_hash": hashed}}
        )
    else:
        history_manager.memory_storage['users'][profile.user_id]['password_hash'] = hashed

    token = create_access_token({"sub": profile.user_id})

    return {
        "access_token": token,
        "user_id": profile.user_id
    }

# ================= LOGIN =================
@app.post("/auth/login")
def login(req: LoginRequest):
    email = str(req.email)
    user = None

    if history_manager.use_mongodb:
        user = history_manager.collection.find_one({"contact.email": email})
    else:
        for u in history_manager.memory_storage['users'].values():
            if u.get('contact', {}).get('email') == email:
                user = u
                break

    if not user or 'password_hash' not in user:
        raise HTTPException(401, "Invalid credentials")

    if not verify_password(req.password, user['password_hash']):
        raise HTTPException(401, "Invalid credentials")

    user_id = user.get("user_id") or str(user.get("_id"))

    token = create_access_token({"sub": user_id})

    return {
        "access_token": token,
        "user_id": user_id
    }

# ================= CHAT =================
@app.post("/api/chat")
async def chat(req: ChatRequest, user_id: str = Depends(get_current_user_id)):
    try:
        return StreamingResponse(
            orchestrator.ask_stream(req.query, user_id=user_id),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(500, str(e))

# ================= ITINERARY SELECTION =================
@app.post("/api/itinerary/select")
def select_itinerary(req: SelectItineraryRequest, user_id: str = Depends(get_current_user_id)):
    temp = orchestrator.temp_itineraries.get(user_id)
    if not temp or 'options' not in temp:
        raise HTTPException(status_code=400, detail="No recently generated itineraries found.")
        
    options = temp['options']
    if req.index < 0 or req.index >= len(options):
        raise HTTPException(status_code=400, detail="Invalid itinerary index.")
        
    strategy_name, full_itinerary = options[req.index]
    trip_details = temp['trip_details']
    
    success = orchestrator.save_selected_itinerary(strategy_name, full_itinerary, trip_details, user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save itinerary.")
        
    return {
        "status": "success", 
        "message": "Itinerary selected and saved successfully.", 
        "strategy": strategy_name
    }

# ================= USER DATA & PROFILE =================
@app.get("/api/user/profile")
def get_user_profile_endpoint(user_id: str = Depends(get_current_user_id)):
    profile = history_manager.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    pref = profile.get('travel_preferences', {})
    contact = profile.get('contact', {})
    
    return {
        "name": profile.get('name', 'User'),
        "email": contact.get('email', 'N/A'),
        "phone": contact.get('phone', 'N/A'),
        "travel_theme": pref.get('activity_interests', ['General'])[0] if pref.get('activity_interests') else 'General',
        "budget_tier": pref.get('comfort_level', 'moderate'),
        "preferences": {
            "cost": int(pref.get('weight_cost', 0.3) * 100),
            "time": int(pref.get('weight_time', 0.2) * 100),
            "preference": int(pref.get('weight_preference', 0.3) * 100),
            "popularity": int(pref.get('weight_popularity', 0.2) * 100),
        }
    }

@app.get("/api/user/trips")
def get_user_trips_endpoint(user_id: str = Depends(get_current_user_id)):
    itineraries = history_manager.get_itineraries(user_id)
    
    trips = []
    for it in itineraries:
        data = it.get('data', it)
        destination = data.get('destination', data.get('destination_city', 'Unknown Destination'))
        
        # build date string gently
        start_dt = data.get('departure_date', '')
        end_dt = data.get('return_date', '')
        dates = f"{start_dt} to {end_dt}".strip(" to ") if start_dt or end_dt else "Flexible Dates"
        
        budget = f"INR {data.get('total_cost_inr', data.get('total_budget_inr', 0)):,.0f}"
        
        # safely extract ID
        trip_id = data.get('trip_id', it.get('_id', str(id(it))))
        
        details = ""
        daily = data.get('daily_schedules', [])
        for day in daily:
            details += f"### Day {day.get('day', '?')}\n"
            for idx, item in enumerate(day.get('items', [])):
                time_val = item.get('time', '')
                time_str = f"**{time_val}**: " if time_val else ""
                details += f"- {time_str}{item.get('name', '')} ({item.get('type', '')})\n"
                desc = item.get('description', '')
                if desc:
                    details += f"  {desc}\n"
                cost = item.get('cost_inr', 0)
                if cost > 0:
                    details += f"  *Cost: INR {cost:,.0f}*\n"
            details += "\n"

        itinerary_obj = {
            "id": str(trip_id),
            "title": f"Trip to {destination}",
            "destination": destination,
            "summary": data.get('query', 'Custom generated itinerary'),
            "budget": budget,
            "days": data.get('num_days', 0),
            "highlights": data.get('interests', []),
            "details": details.strip() or "No detailed schedule available.",
            "created_at": str(it.get('created_at', ''))
        }
        
        trips.append({
            "id": str(trip_id),
            "destination": destination,
            "dates": dates,
            "budget": budget,
            "status": "planned",
            "itinerary": itinerary_obj
        })
        
    return trips

# ================= FEEDBACK PIPELINE =================
@app.post("/api/update_feedback")
def update_feedback(req: ModelFeedbackRequest):
    # Step 2: Store feedback in DB
    history_manager.store_raw_feedback(req.user_id, req.trip_id, req.feedback)
    
    # Step 3: Predict weights from textual feedback using SentenceTransformers + Random Forest
    deltas = predictor.predict_weights_delta(req.feedback)
    
    # Step 4, 5, 6, 7: Fetch existing weights, Apply LR update, Clamp, Normalize, Log, Save
    if deltas:
        new_weights = history_manager.update_optimizer_weights(req.user_id, deltas)
        return {
            "status": "success", 
            "predicted_deltas": deltas, 
            "new_weights": new_weights
        }
    else:
        # Fallback requirement: safely store but don't break
        return {"status": "stored_only", "message": "Feedback safely stored, but NLP prediction failed"}

# ================= FRONTEND =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Travel Planner</title>
<style>
body { font-family: Arial; background:#f4f7fb; display:flex; justify-content:center; }
.container { width:600px; background:white; padding:20px; margin-top:50px; border-radius:10px;}
.page { display:none; }
.page.active { display:block; }
button { padding:10px; width:100%; margin-top:10px; }
.messages { height:300px; overflow:auto; border:1px solid #ccc; margin:10px 0; padding:10px;}
.bubble { margin:5px; padding:8px; border-radius:10px;}
.user { background:#dbe8ff; text-align:right;}
.bot { background:#e8f7e4;}
</style>
</head>
<body>

<div class="container">

<div id="loginPage" class="page active">
<h2>Login</h2>
<input id="loginEmail" placeholder="email"><br>
<input id="loginPassword" type="password" placeholder="password"><br>
<button onclick="login()">Login</button>
<button onclick="switchPage('signupPage')">Signup</button>
</div>

<div id="signupPage" class="page">
<h2>Signup</h2>
<input id="suName" placeholder="name"><br>
<input id="suEmail" placeholder="email"><br>
<input id="suPhone" placeholder="phone"><br>
<input id="suPassword" type="password" placeholder="password"><br>
<select id="suTheme">
<option value="nature">Nature</option>
<option value="adventure">Adventure</option>
</select>
<select id="suBudget">
<option value="budget">Budget</option>
<option value="moderate">Moderate</option>
</select>
<button onclick="signup()">Create</button>
</div>

<div id="chatPage" class="page">
<button onclick="logout()">Logout</button>
<div id="messages" class="messages"></div>
<input id="queryInput" placeholder="Ask...">
<button onclick="sendMessage()">Send</button>

<hr style="margin-top:20px;">
<div style="background:#e8f0fe; padding:15px; border-radius:10px; margin-top:20px;">
<h4>Submit Post-Trip Feedback (ML Auto-Tunes Preferences)</h4>
<input id="tripIdInput" value="trip_789" style="padding:5px; width:100%; box-sizing:border-box;"><br><br>
<textarea id="feedbackInput" rows="3" style="width:100%; padding:5px; box-sizing:border-box;" placeholder="e.g. Trip was expensive and too rushed but I loved hidden gems"></textarea>
<button style="background:#28a745; color:#fff;" onclick="sendFeedback()">Submit Feedback</button>
<pre id="feedbackResult" style="font-size:12px; overflow-x:auto; margin-top:10px;"></pre>
</div>

</div>

</div>

<script>
let token = localStorage.getItem("token");

if(token) switchPage('chatPage');

function switchPage(id){
document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
document.getElementById(id).classList.add('active');
}

function logout(){
localStorage.removeItem("token");
token=null;
switchPage('loginPage');
}

async function apiCall(url,data,auth=false){
const headers={'Content-Type':'application/json'};
if(auth) headers['Authorization']='Bearer '+token;

const res=await fetch(url,{method:'POST',headers,body:JSON.stringify(data)});
const d=await res.json();
if(!res.ok) throw new Error(d.detail);
return d;
}

async function login(){
try{
const d=await apiCall('/auth/login',{
email:loginEmail.value,
password:loginPassword.value
});
token=d.access_token;
localStorage.setItem("token",token);
switchPage('chatPage');
}catch(e){alert(e.message);}
}

async function signup(){
try{
const d=await apiCall('/auth/signup',{
name:suName.value,
email:suEmail.value,
phone:suPhone.value,
password:suPassword.value,
travel_theme:suTheme.value,
budget_tier:suBudget.value
});
token=d.access_token;
localStorage.setItem("token",token);
switchPage('chatPage');
}catch(e){alert(e.message);}
}

function addBubble(t,u){
const d=document.createElement('div');
d.className='bubble '+(u?'user':'bot');
d.innerHTML=t;
messages.appendChild(d);
}

async function sendMessage(){
const q=queryInput.value;
addBubble(q,true);

const res=await fetch('/api/chat',{
method:'POST',
headers:{'Content-Type':'application/json','Authorization':'Bearer '+token},
body:JSON.stringify({query:q})
});

const reader=res.body.getReader();
const decoder=new TextDecoder();
let txt='';
const div=document.createElement('div');
div.className='bubble bot';
messages.appendChild(div);

while(true){
const {done,value}=await reader.read();
if(done) break;
txt+=decoder.decode(value);
div.innerHTML=txt;
}
}

async function sendFeedback(){
try {
    let uid = "anonymous";
    if (token) {
        const payloadStr = atob(token.split('.')[1]);
        uid = JSON.parse(payloadStr).sub;
    }
    const data = await apiCall('/api/update_feedback', {
        user_id: uid,
        trip_id: document.getElementById('tripIdInput').value || 'trip_unknown',
        feedback: document.getElementById('feedbackInput').value || 'Good trip'
    }, true);
    document.getElementById('feedbackResult').innerText = JSON.stringify(data, null, 2);
} catch(e) {
    document.getElementById('feedbackResult').innerText = "Error: " + e.message;
}
}
</script>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

# ================= RUN =================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=True)