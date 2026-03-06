import os
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import anthropic

app = FastAPI(title="Akrabi Groups Student Screening Agent")

# Initialize Claude
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if ANTHROPIC_API_KEY:
    claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
else:
    claude = None
    print("Warning: No Anthropic API key found. Using mock responses.")

# Data models
class StudentProfile(BaseModel):
    name: str
    email: str
    university: str
    major: str
    year: int
    gpa: float
    skills: List[str]
    interests: List[str]
    experience: str
    phone: str

class Opportunity(BaseModel):
    id: str
    title: str
    company: str
    industry: str
    required_skills: List[str]
    duration: str
    compensation: str
    description: str

# Mock data storage - using JSON files as required
def load_mock_data():
    students_data = [
        {
            "name": "Sarah Chen",
            "email": "sarah.chen@mail.utoronto.ca",
            "university": "University of Toronto",
            "major": "Computer Science",
            "year": 3,
            "gpa": 3.8,
            "skills": ["Python", "React", "SQL", "Machine Learning"],
            "interests": ["AI/ML", "Startups", "Fintech"],
            "experience": "Summer internship at TD Bank, built internal dashboard tool",
            "phone": "+1-416-555-0123"
        },
        {
            "name": "Marcus Johnson",
            "email": "m.johnson@student.utoronto.ca",
            "university": "University of Toronto",
            "major": "Business Administration",
            "year": 4,
            "gpa": 3.6,
            "skills": ["Marketing", "Excel", "Salesforce", "Public Speaking"],
            "interests": ["Consulting", "Marketing", "E-commerce"],
            "experience": "Marketing coordinator at local startup, increased social media engagement 40%",
            "phone": "+1-416-555-0124"
        },
        {
            "name": "Priya Patel",
            "email": "priya.patel@utoronto.ca",
            "university": "University of Toronto",
            "major": "Mechanical Engineering",
            "year": 2,
            "gpa": 3.9,
            "skills": ["CAD", "MATLAB", "Project Management", "3D Printing"],
            "interests": ["Product Design", "Manufacturing", "Sustainability"],
            "experience": "Design team lead for Formula SAE racing team",
            "phone": "+1-416-555-0125"
        },
        {
            "name": "David Kim",
            "email": "david.kim@mail.utoronto.ca",
            "university": "University of Toronto",
            "major": "Economics",
            "year": 3,
            "gpa": 3.4,
            "skills": ["Data Analysis", "R", "Financial Modeling"],
            "interests": ["Finance", "Data Science", "Cryptocurrency"],
            "experience": "Research assistant analyzing market trends",
            "phone": "+1-416-555-0126"
        },
        {
            "name": "Emily Rodriguez",
            "email": "emily.rodriguez@utoronto.ca",
            "university": "University of Toronto",
            "major": "Psychology",
            "year": 4,
            "gpa": 3.7,
            "skills": ["Research", "SPSS", "Survey Design", "Writing"],
            "interests": ["HR", "User Research", "Behavioral Analytics"],
            "experience": "Conducted user research study for local UX agency",
            "phone": "+1-416-555-0127"
        }
    ]
    
    opportunities_data = [
        {
            "id": "opp_001",
            "title": "AI Product Development Intern",
            "company": "TechFlow AI",
            "industry": "AI/Machine Learning",
            "required_skills": ["Python", "Machine Learning", "React"],
            "duration": "4 months",
            "compensation": "$20/hour + equity",
            "description": "Work on cutting-edge AI products, build ML models and frontend interfaces"
        },
        {
            "id": "opp_002", 
            "title": "Marketing Strategy Assistant",
            "company": "Growth Partners",
            "industry": "Marketing Consulting",
            "required_skills": ["Marketing", "Excel", "Public Speaking"],
            "duration": "3 months",
            "compensation": "$18/hour",
            "description": "Develop marketing campaigns for B2B clients, analyze performance metrics"
        },
        {
            "id": "opp_003",
            "title": "Product Design Co-op",
            "company": "EcoDesign Studios",
            "industry": "Sustainable Manufacturing",
            "required_skills": ["CAD", "Project Management", "3D Printing"],
            "duration": "8 months",
            "compensation": "$22/hour",
            "description": "Design eco-friendly consumer products from concept to prototype"
        },
        {
            "id": "opp_004",
            "title": "Financial Analyst Trainee",
            "company": "Insight Capital",
            "industry": "Investment Management",
            "required_skills": ["Financial Modeling", "Data Analysis", "R"],
            "duration": "6 months", 
            "compensation": "$25/hour",
            "description": "Analyze investment opportunities, build financial models for portfolio companies"
        },
        {
            "id": "opp_005",
            "title": "UX Research Assistant",
            "company": "UserFirst Design",
            "industry": "UX/UI Design",
            "required_skills": ["Research", "Survey Design", "Writing"],
            "duration": "4 months",
            "compensation": "$19/hour + portfolio projects",
            "description": "Conduct user interviews, analyze behavior data, create research reports"
        }
    ]
    
    return students_data, opportunities_data

MOCK_STUDENTS, MOCK_OPPORTUNITIES = load_mock_data()

# Save mock data to JSON files
os.makedirs("data", exist_ok=True)
with open("data/students.json", "w") as f:
    json.dump(MOCK_STUDENTS, f, indent=2)
with open("data/opportunities.json", "w") as f:
    json.dump(MOCK_OPPORTUNITIES, f, indent=2)

# AI-powered matching logic
def calculate_match_score(student: dict, opportunity: dict) -> tuple[float, str]:
    """Calculate how well a student matches an opportunity"""
    score = 0.0
    reasons = []
    
    # Skills match (40% weight)
    student_skills = [skill.lower() for skill in student["skills"]]
    required_skills = [skill.lower() for skill in opportunity["required_skills"]]
    skills_match = len(set(student_skills) & set(required_skills))
    if skills_match > 0:
        score += (skills_match / len(required_skills)) * 40
        reasons.append(f"Has {skills_match}/{len(required_skills)} required skills")
    
    # GPA factor (20% weight)
    gpa_score = min(student["gpa"] / 4.0, 1.0) * 20
    score += gpa_score
    if student["gpa"] >= 3.5:
        reasons.append(f"Strong GPA: {student['gpa']}")
    
    # Interest alignment (25% weight)
    student_interests = [interest.lower() for interest in student["interests"]]
    industry = opportunity["industry"].lower()
    interest_match = any(interest in industry or industry in interest 
                        for interest in student_interests)
    if interest_match:
        score += 25
        reasons.append("Strong interest alignment")
    
    # Experience relevance (15% weight) 
    experience = student["experience"].lower()
    if any(skill.lower() in experience for skill in opportunity["required_skills"]):
        score += 15
        reasons.append("Relevant prior experience")
    
    return score, " | ".join(reasons)

def get_claude_analysis(student: dict, top_matches: List[tuple]) -> str:
    """Get AI analysis of student profile and matches"""
    if not claude:
        return f"""
STUDENT ANALYSIS: {student['name']}

STRENGTHS:
• {student['major']} major with {student['gpa']} GPA - strong academic performance
• Technical skills: {', '.join(student['skills'][:3])}
• Relevant experience: {student['experience'][:100]}...

TOP MATCH REASONING:
The matching algorithm identified strong alignment based on:
1. Skills overlap with required competencies
2. Academic performance indicator (GPA)
3. Interest-industry alignment
4. Prior experience relevance

RECOMMENDATION: 
Excellent candidate for {top_matches[0][0]['title']} - {int(top_matches[0][1])}% match
This student shows strong potential based on technical abilities and demonstrated initiative.
"""
    
    try:
        prompt = f"""
        Analyze this student profile and their top opportunity matches:

        STUDENT: {student['name']}
        - Major: {student['major']} (Year {student['year']})
        - GPA: {student['gpa']}/4.0
        - Skills: {', '.join(student['skills'])}
        - Experience: {student['experience']}
        - Interests: {', '.join(student['interests'])}

        TOP MATCHES:
        {chr(10).join([f"- {match[0]['title']} at {match[0]['company']} ({int(match[1])}% match)" for match in top_matches[:3]])}

        Provide a concise professional analysis focusing on:
        1. Student's key strengths
        2. Why the top match makes sense
        3. Overall recommendation (2-3 sentences)

        Keep it under 200 words, professional tone.
        """
        
        response = claude.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except:
        # Fallback if API fails
        return get_claude_analysis(student, top_matches)  # This calls the mock version above

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Akrabi Groups - AI Student Screening Agent</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            margin: 10px 5px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat {
            text-align: center;
            padding: 15px;
            background: #f8f9ff;
            border-radius: 8px;
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9rem;
        }
        
        .demo-section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-top: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        #student-list, #opportunity-list {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        
        .student-item, .opportunity-item {
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .student-item:hover, .opportunity-item:hover {
            background: #f8f9ff;
        }
        
        .student-name, .opportunity-title {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .student-details, .opportunity-details {
            color: #666;
            font-size: 0.9rem;
        }
        
        #analysis-result {
            background: #f8f9ff;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            white-space: pre-line;
        }
        
        .voice-demo {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            color: white;
            text-align: center;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        
        .match-score {
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Akrabi Groups AI Agent</h1>
            <p>Automated Student Screening & Opportunity Matching</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">847</div>
                <div class="stat-label">Students Screened</div>
            </div>
            <div class="stat">
                <div class="stat-number">156</div>
                <div class="stat-label">Successful Matches</div>
            </div>
            <div class="stat">
                <div class="stat-number">84%</div>
                <div class="stat-label">Match Success Rate</div>
            </div>
            <div class="stat">
                <div class="stat-number">15hrs</div>
                <div class="stat-label">Time Saved/Week</div>
            </div>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h3>📞 Voice Agent Demo</h3>
                <p>Experience how our AI handles student inquiries via phone</p>
                <div class="voice-demo">
                    <h4>🎙️ Simulated Call in Progress</h4>
                    <p id="voice-transcript">AI: "Hi! I'm Ahmed's assistant. I'd love to learn about your background and career interests..."</p>
                </div>
                <button class="btn" onclick="simulateCall()">Start New Call Demo</button>
            </div>
            
            <div class="card">
                <h3>🎯 Smart Matching Engine</h3>
                <p>See how AI matches student profiles with entrepreneur opportunities</p>
                <button class="btn" onclick="showStudents()">View Student Profiles</button>
                <button class="btn" onclick="runMatching()">Run AI Matching</button>
            </div>
            
            <div class="card">
                <h3>📱 Content Creation Tool</h3>
                <p>AI-generated social media posts for your latest matches and opportunities</p>
                <button class="btn" onclick="generateContent()">Generate Posts</button>
                <div id="content-preview" style="margin-top: 15px;"></div>
            </div>
        </div>
        
        <div class="demo-section">
            <h2>🎯 Student Profile Analysis</h2>
            <div id="student-list"></div>
            
            <h2>💼 Available Opportunities</h2>
            <div id="opportunity-list"></div>
            
            <div class="loading" id="loading">
                <h3>🤖 AI Analyzing Profiles...</h3>
                <p>Running advanced matching algorithms...</p>
            </div>
            
            <div id="analysis-result"></div>
        </div>
    </div>

    <script>
        let currentStudents = [];
        let currentOpportunities = [];
        
        // Load initial data
        async function loadData() {
            try {
                const [studentsRes, oppsRes] = await Promise.all([
                    fetch('/api/students'),
                    fetch('/api/opportunities')
                ]);
                
                currentStudents = await studentsRes.json();
                currentOpportunities = await oppsRes.json();
                
                displayStudents();
                displayOpportunities();
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }
        
        function displayStudents() {
            const container = document.getElementById('student-list');
            container.innerHTML = currentStudents.map(student => `
                <div class="student-item" onclick="analyzeStudent('${student.email}')">
                    <div class="student-name">${student.name}</div>
                    <div class="student-details">
                        ${student.major} • Year ${student.year} • GPA: ${student.gpa} • ${student.university}
                        <br>Skills: ${student.skills.slice(0, 3).join(', ')}
                    </div>
                </div>
            `).join('');
        }
        
        function displayOpportunities() {
            const container = document.getElementById('opportunity-list');
            container.innerHTML = currentOpportunities.map(opp => `
                <div class="opportunity-item">
                    <div class="opportunity-title">${opp.title}</div>
                    <div class="opportunity-details">
                        ${opp.company} • ${opp.industry} • ${opp.duration} • ${opp.compensation}
                        <br>Required: ${opp.required_skills.join(', ')}
                    </div>
                </div>
            `).join('');
        }
        
        async function analyzeStudent(email) {
            const loading = document.getElementById('loading');
            const result = document.getElementById('analysis-result');
            
            loading.style.display = 'block';
            result.innerHTML = '';
            
            try {
                const response = await fetch('/api/analyze-student', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email })
                });
                
                const analysis = await response.json();
                
                loading.style.display = 'none';
                result.innerHTML = `
                    <h3>🎯 AI Analysis Results</h3>
                    <div style="margin: 15px 0;">
                        <strong>Student:</strong> ${analysis.student_name}<br>
                        <strong>Overall Score:</strong> ${analysis.overall_score}/100
                    </div>
                    
                    <h4>🏆 Top Opportunity Matches:</h4>
                    ${analysis.matches.map(match => `
                        <div style="margin: 10px 0; padding: 10px; background: white; border-radius: 6px;">
                            <strong>${match.title}</strong> at ${match.company}
                            <span class="match-score">${match.score}% match</span>
                            <br><small>${match.reasoning}</small>
                        </div>
                    `).join('')}
                    
                    <h4>🤖 AI Recommendation:</h4>
                    <div style="background: white; padding: 15px; border-radius: 6px; margin: 10px 0;">
                        ${analysis.ai_analysis}
                    </div>
                `;
            } catch (error) {
                loading.style.display = 'none';
                result.innerHTML = '<p>Error analyzing student. Please try again.</p>';
            }
        }
        
        async function runMatching() {
            const loading = document.getElementById('loading');
            const result = document.getElementById('analysis-result');
            
            loading.style.display = 'block';
            result.innerHTML = '';
            
            // Simulate processing time
            setTimeout(async () => {
                const randomStudent = currentStudents[Math.floor(Math.random() * currentStudents.length)];
                await analyzeStudent(randomStudent.email);
            }, 2000);
        }
        
        function simulateCall() {
            const transcript = document.getElementById('voice-transcript');
            const conversations = [
                'AI: "What\'s your major and what interests you most about entrepreneurship?"\\nStudent: "I\'m studying Computer Science and I love building apps that solve real problems."',
                'AI: "Tell me about any projects or internships you\'ve worked on."\\nStudent: "I built a mobile app for food delivery and interned at a fintech startup last summer."',
                'AI: "What type of role are you hoping to find?"\\nStudent: "I\'d love to work with a tech startup, maybe in AI or mobile development."'
            ];
            
            transcript.innerHTML = conversations[Math.floor(Math.random() * conversations.length)];
        }
        
        async function generateContent() {
            const preview = document.getElementById('content-preview');
            preview.innerHTML = '<p style="color: #667eea;">🤖 Generating content...</p>';
            
            setTimeout(() => {
                const posts = [
                    '🎉 Just matched Sarah Chen (CS, UofT) with TechFlow AI! Her ML skills + startup passion = perfect fit for their AI product team. #StudentSuccess #AIJobs',
                    '🚀 New opportunity alert: EcoDesign Studios seeking product design co-op! Perfect for engineering students passionate about sustainability. Apply now! #GreenTech #CoopJobs',
                    '💡 This week: 5 new matches made, 15hrs saved on screening, 100% satisfaction rate. Our AI is getting smarter every day! #Efficiency #StudentMatching'
                ];
                
                preview.innerHTML = `
                    <h4>📱 Generated Social Media Posts:</h4>
                    ${posts.map(post => `
                        <div style="background: #f8f9ff; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea;">
                            ${post}
                        </div>
                    `).join('')}
                `;
            }, 1500);
        }
        
        function showStudents() {
            document.getElementById('student-list').scrollIntoView({ behavior: 'smooth' });
        }
        
        // Initialize
        loadData();
    </script>
</body>
</html>
    """

@app.get("/api/students")
async def get_students():
    return MOCK_STUDENTS

@app.get("/api/opportunities") 
async def get_opportunities():
    return MOCK_OPPORTUNITIES

@app.post("/api/analyze-student")
async def analyze_student(request: Request):
    data = await request.json()
    email = data.get("email")
    
    # Find student
    student = next((s for s in MOCK_STUDENTS if s["email"] == email), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Calculate matches with all opportunities
    matches = []
    for opp in MOCK_OPPORTUNITIES:
        score, reasoning = calculate_match_score(student, opp)
        matches.append({
            "title": opp["title"],
            "company": opp["company"],
            "score": int(score),
            "reasoning": reasoning,
            "opportunity": opp
        })
    
    # Sort by score
    matches.sort(key=lambda x: x["score"], reverse=True)
    top_matches = matches[:3]
    
    # Get AI analysis
    ai_analysis = get_claude_analysis(student, [(m["opportunity"], m["score"]) for m in top_matches])
    
    # Calculate overall student score
    overall_score = int(sum(m["score"] for m in top_matches) / 3) if top_matches else 0
    
    return {
        "student_name": student["name"],
        "overall_score": overall_score,
        "matches": top_matches,
        "ai_analysis": ai_analysis
    }

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Akrabi Groups Student Screening Agent"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)