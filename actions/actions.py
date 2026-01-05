import csv
import os
from rapidfuzz import process
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from typing import Any, Text, Dict, List

class ActionViewCourses(Action):
    """Display all available courses with helpful buttons"""
    
    def name(self):
        return "action_view_courses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        csv_path = os.path.join(os.path.dirname(__file__), "course_data.csv")

        if not os.path.exists(csv_path):
            dispatcher.utter_message(
                text="⚠️ Course database not found."
            )
            return []

        courses = []
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                courses.append({
                    'name': row['course_name'],
                    'duration': row['duration'],
                    'level': row['suitable_for'].split('|')[0] if '|' in row['suitable_for'] else row['suitable_for']
                })

        if not courses:
            dispatcher.utter_message(
                text="No courses are available right now."
            )
            return []

        # Build course list with duration and level
        course_items = []
        for idx, course in enumerate(courses, 1):
            course_items.append(
                f"{idx}. <b>{course['name']}</b><br>"
                f"   ⏱️ {course['duration']} | 📊 {course['level']}"
            )
        
        course_list = "<br><br>".join(course_items)

        message = (
            "<b>📚 Available Courses at ICTAK</b><br><br>"
            f"{course_list}<br><br>"
            "💡 <b>What would you like to do next?</b>"
        )

        # Suggestion buttons
        buttons = [
            {"title": "🧭 Help Me Choose", "payload": "/start_course_advisor"},
            {"title": "🔍 Search Course", "payload": "tell me about"},
            {"title": "📞 Talk to Counselor", "payload": "/ask_contact"},
            {"title": "💼 Placement Info", "payload": "/ask_placement"},
            {"title": "🎓 Scholarships", "payload": "/ask_scholarships"}
        ]

        dispatcher.utter_message(text=message, buttons=buttons)

        return []


class ActionCourseInfo(Action):
    """Show detailed information about a specific course"""
    
    def name(self):
        return "action_course_info"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict
    ):
        # Get latest user message
        user_message = tracker.latest_message.get("text", "").lower()

        # CSV path
        csv_path = os.path.join(os.path.dirname(__file__), "course_data.csv")

        if not os.path.exists(csv_path):
            dispatcher.utter_message(
                text="⚠️ Course database not found. Please contact support."
            )
            return []

        # Load courses
        courses = {}
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                courses[row["course_name"].lower()] = row

        if not courses:
            dispatcher.utter_message(text="No courses available at the moment.")
            return []

        # Fuzzy match user input
        best_match, score, _ = process.extractOne(user_message, courses.keys())

        if score >= 70:
            course = courses[best_match]
            
            # Extract key skills (first 5)
            skills_list = course.get('key_skills', '').split('|')[:5]
            skills_text = '<br>• '.join(skills_list)

            response = (
                f"<b>📚 {course['course_name']}</b><br><br>"
                f"<b>📖 Description:</b><br>{course['description']}<br><br>"
                f"<b>⏱️ Duration:</b> {course['duration']}<br>"
                f"<b>💰 Fees:</b> {course['fees']}<br>"
                f"<b>📊 Suitable For:</b> {course['suitable_for'].replace('|', ', ')}<br><br>"
                f"<b>🔑 Key Skills:</b><br>• {skills_text}<br><br>"
                f"💡 <b>What would you like to know?</b>"
            )
            
            # Suggestion buttons
            buttons = [
                {"title": "💼 Career & Salary", "payload": "/request_career_info"},
                {"title": "🧭 Is This Right for Me?", "payload": "/start_course_advisor"},
                {"title": "📊 Compare Courses", "payload": "/view_courses"},
                {"title": "✅ I'm Interested", "payload": "/ask_contact"},
                {"title": "🎓 Scholarships", "payload": "/ask_scholarships"}
            ]

        else:
            # Course not found - show helpful options
            response = (
                "❌ I couldn't identify that course.<br><br>"
                "💡 <b>Try one of these:</b><br>"
                "• Type: <i>\"Data Science\"</i><br>"
                "• Type: <i>\"Artificial Intelligence\"</i><br>"
                "• Type: <i>\"Full Stack\"</i><br>"
                "• Type: <i>\"Cyber Security\"</i><br>"
                "• Type: <i>\"SDET\"</i><br><br>"
                "Or let me help you choose!"
            )
            
            buttons = [
                {"title": "🧭 Help Me Choose", "payload": "/start_course_advisor"},
                {"title": "📚 View All Courses", "payload": "/view_courses"},
                {"title": "📞 Talk to Counselor", "payload": "/ask_contact"}
            ]

        dispatcher.utter_message(text=response, buttons=buttons)

        return []


class ActionCompareCourses(Action):
    """NEW: Compare multiple courses side by side"""
    
    def name(self):
        return "action_compare_courses"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        
        csv_path = os.path.join(os.path.dirname(__file__), "course_data.csv")
        
        if not os.path.exists(csv_path):
            dispatcher.utter_message(text="⚠️ Course database not found.")
            return []
        
        courses = []
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                courses.append(row)
        
        if not courses:
            dispatcher.utter_message(text="No courses available.")
            return []
        
        # Build comparison table
        message = "<b>📊 Course Comparison</b><br><br>"
        
        for course in courses:
            # Get first salary range
            salary = course.get('job_roles_salary', 'Contact ICTAK').split('|')[0]
            
            message += (
                f"<b>{course['course_name']}</b><br>"
                f"⏱️ Duration: {course['duration']}<br>"
                f"💰 Fees: {course['fees']}<br>"
                f"📊 Level: {course['suitable_for'].split('|')[0]}<br>"
                f"💼 Salary: {salary}<br><br>"
            )
        
        message += "💡 <b>Need help deciding?</b>"
        
        buttons = [
            {"title": "🧭 Find My Perfect Match", "payload": "/start_course_advisor"},
            {"title": "🔍 Search Specific Course", "payload": "tell me about"},
            {"title": "📞 Talk to Counselor", "payload": "/ask_contact"}
        ]
        
        dispatcher.utter_message(text=message, buttons=buttons)
        
        return []

class ActionRecommendCourse(Action):
    """Smart course recommendation - Simplified version"""
    
    def name(self) -> Text:
        return "action_recommend_course"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get user profile
        goal = tracker.get_slot("user_goal")
        experience = tracker.get_slot("user_experience")
        interest = tracker.get_slot("user_interest")
        career_role = tracker.get_slot("user_career_role")
        
        # Check if user is unsure about key decisions
        is_interest_unsure = interest and 'unsure' in interest.lower()
        is_role_unsure = career_role and 'unsure' in career_role.lower()
        
        # If both interest AND role are unsure, ask discovery questions
        if is_interest_unsure and is_role_unsure:
            return self.handle_unsure_user(dispatcher, experience, goal)
        
        # If only interest is unsure but role is clear, infer from role
        if is_interest_unsure and not is_role_unsure:
            interest = self.infer_interest_from_role(career_role)
        
        # If only role is unsure but interest is clear, continue with interest
        if is_role_unsure and not is_interest_unsure:
            career_role = "general"
        
        # Load courses from CSV
        csv_path = os.path.join(os.path.dirname(__file__), "course_data.csv")
        
        if not os.path.exists(csv_path):
            dispatcher.utter_message(text="⚠️ Course database not found.")
            return []
        
        courses = []
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                courses.append(row)
        
        if not courses:
            dispatcher.utter_message(text="No courses available.")
            return []
        
        # Score each course
        scored_courses = []
        for course in courses:
            score = self.calculate_match_score(
                course, interest, career_role, experience, goal
            )
            scored_courses.append((course, score))
        
        # Get top recommendation
        scored_courses.sort(key=lambda x: x[1], reverse=True)
        top_course, top_score = scored_courses[0]
        second_course, second_score = scored_courses[1] if len(scored_courses) > 1 else (None, 0)
        
        # Generate simplified response
        match_level = "Excellent" if top_score >= 80 else "Great" if top_score >= 60 else "Good"
        
        # Extract key skills (first 5)
        skills_list = top_course.get('key_skills', '').split('|')[:5]
        skills_text = '<br>• '.join(skills_list)
        
        # SIMPLIFIED MESSAGE - Removed About, Career Paths, Salary
        message = (
            f"<b>🎯 Your Personalized Recommendation</b><br><br>"
            f"<b>📚 {top_course['course_name']}</b><br>"
            f"✅ Match Score: {top_score}% - {match_level} fit!<br><br>"
            f"<b>Why this course?</b><br>"
            f"{self.get_reasoning(interest, career_role, experience, goal)}<br><br>"
            f"<b>⏱️ Duration:</b> {top_course['duration']}<br>"
            f"<b>💰 Fees:</b> {top_course['fees']}<br>"
            f"<b>📊 Level:</b> {top_course['suitable_for'].replace('|', ', ')}<br><br>"
            f"<b>🔑 Key Skills:</b><br>• {skills_text}<br><br>"
        )
        
        # Add second best if close in score
        if second_course and (top_score - second_score) < 20:
            message += (
                f"<b>💡 Alternative:</b> {second_course['course_name']} ({second_score}% match)<br><br>"
            )
        
        message += "Want to know more about this course?"
        
        dispatcher.utter_message(
            text=message,
            buttons=[
                {"title": "📖 Full Course Details", "payload": "/request_more_info"},
                {"title": "💼 Career & Salary Info", "payload": "/request_career_info"},
                {"title": "📊 Compare Courses", "payload": "/view_courses"},
                {"title": "📞 Contact ICTAK", "payload": "/ask_contact"}
            ]
        )
        
        return [SlotSet("recommended_course", top_course['course_name'])]
    
    def handle_unsure_user(self, dispatcher, experience, goal):
        """Handle users who are unsure about both interest and role"""
        
        if experience and experience == 'advanced':
            message = (
                "<b>🤔 I see you're exploring options!</b><br><br>"
                "Since you have <b>advanced coding experience</b> and want a <b>career change</b>, "
                "let me help you discover the best path.<br><br>"
                "<b>💡 Quick Discovery Question:</b><br>"
                "What type of work excites you more?"
            )
            
            dispatcher.utter_message(
                text=message,
                buttons=[
                    {"title": "🤖 Building intelligent AI systems", "payload": '/inform_interest{"interest_area":"ai ml"}'},
                    {"title": "📊 Analyzing data for insights", "payload": '/inform_interest{"interest_area":"data science"}'},
                    {"title": "💻 Creating modern web applications", "payload": '/inform_interest{"interest_area":"full stack"}'},
                    {"title": "🔒 Securing systems from threats", "payload": '/inform_interest{"interest_area":"cybersecurity"}'},
                    {"title": "🧪 Ensuring software quality", "payload": '/inform_interest{"interest_area":"testing"}'}
                ]
            )
            return []
        
        else:
            message = (
                "<b>🤔 Let me help you discover the right path!</b><br><br>"
                "Since you're exploring career change options, let's find what matches your interests.<br><br>"
                "<b>💡 Quick Question:</b><br>"
                "Do you prefer working with:"
            )
            
            dispatcher.utter_message(
                text=message,
                buttons=[
                    {"title": "📊 Numbers, data, and patterns", "payload": '/inform_interest{"interest_area":"data science"}'},
                    {"title": "💻 Building websites and apps", "payload": '/inform_interest{"interest_area":"full stack"}'},
                    {"title": "🤖 Artificial Intelligence", "payload": '/inform_interest{"interest_area":"ai ml"}'},
                    {"title": "🔒 Security and protection", "payload": '/inform_interest{"interest_area":"cybersecurity"}'},
                    {"title": "📚 Show me all options", "payload": "/view_courses"}
                ]
            )
            return []
    
    def infer_interest_from_role(self, career_role):
        """Infer interest area from career role when interest is unsure"""
        role_lower = career_role.lower()
        
        if any(keyword in role_lower for keyword in ['ml', 'ai']):
            return "ai ml"
        elif 'data scientist' in role_lower:
            return "data science"
        elif 'data analyst' in role_lower:
            return "data science"
        elif any(keyword in role_lower for keyword in ['full stack', 'web', 'frontend', 'backend']):
            return "full stack"
        elif any(keyword in role_lower for keyword in ['security', 'cyber']):
            return "cybersecurity"
        elif any(keyword in role_lower for keyword in ['sdet', 'qa', 'test']):
            return "testing"
        else:
            return "data science"
    
    def calculate_match_score(self, course, interest, career_role, experience, goal):
        """Calculate match score for ICTAK courses"""
        score = 0
        course_name_lower = course['course_name'].lower()
        focus_areas_lower = course['focus_areas'].lower()
        career_paths = course.get('career_paths', '').lower()
        
        # Interest matching (40 points)
        if interest:
            interest_lower = interest.lower()
            
            if any(keyword in interest_lower for keyword in ['ai', 'ml', 'machine learning', 'artificial intelligence', 'deep learning', 'intelligent']):
                if 'artificial intelligence' in course_name_lower or 'machine learning' in course_name_lower:
                    score += 40
                elif 'data science' in course_name_lower:
                    score += 25
            
            elif any(keyword in interest_lower for keyword in ['data', 'analytics', 'insights', 'statistics', 'numbers', 'patterns']):
                if 'data science' in course_name_lower:
                    score += 40
                elif 'artificial intelligence' in course_name_lower:
                    score += 25
            
            elif any(keyword in interest_lower for keyword in ['web', 'website', 'apps', 'development', 'frontend', 'backend', 'full stack', 'building', 'creating']):
                if 'full stack' in course_name_lower or 'mern' in course_name_lower:
                    score += 40
            
            elif any(keyword in interest_lower for keyword in ['testing', 'qa', 'quality', 'automation', 'sdet', 'ensuring']):
                if 'sdet' in course_name_lower:
                    score += 40
            
            elif any(keyword in interest_lower for keyword in ['security', 'cyber', 'hacking', 'protection', 'cybersecurity', 'securing', 'threats']):
                if 'cyber' in course_name_lower or 'security' in course_name_lower:
                    score += 40
            
            elif 'unsure' in interest_lower or interest_lower == 'general':
                if 'data science' in course_name_lower or 'full stack' in course_name_lower:
                    score += 25
        
        # Career role matching (30 points)
        if career_role and 'unsure' not in career_role.lower() and career_role != 'general':
            role_lower = career_role.lower()
            
            if any(keyword in role_lower for keyword in ['data scientist', 'ml engineer', 'ai']):
                if 'artificial intelligence' in course_name_lower:
                    score += 30
                elif 'data science' in course_name_lower:
                    score += 25
            
            elif 'data analyst' in role_lower:
                if 'data science' in course_name_lower:
                    score += 30
            
            elif any(keyword in role_lower for keyword in ['full stack', 'web developer', 'mern', 'frontend', 'backend']):
                if 'full stack' in course_name_lower or 'mern' in course_name_lower:
                    score += 30
            
            elif any(keyword in role_lower for keyword in ['sdet', 'test', 'qa', 'quality']):
                if 'sdet' in course_name_lower:
                    score += 30
            
            elif any(keyword in role_lower for keyword in ['security', 'cyber']):
                if 'cyber' in course_name_lower or 'security' in course_name_lower:
                    score += 30
            
            if career_paths and any(keyword in career_paths for keyword in role_lower.split()):
                score += 15
        
        # Experience level matching (20 points)
        if experience:
            suitable_levels = course.get('suitable_for', '').lower()
            
            if experience in suitable_levels:
                score += 20
            elif experience == 'beginner' and 'basic' in suitable_levels:
                score += 18
            elif experience == 'basic' and 'beginner' in suitable_levels:
                score += 18
            elif experience == 'beginner' and not any(x in suitable_levels for x in ['beginner', 'basic']):
                score += 5
            elif experience == 'advanced':
                if 'artificial intelligence' in course_name_lower or 'data science' in course_name_lower:
                    score += 25
                else:
                    score += 15
            else:
                score += 10
        
        # Goal alignment (10 points)
        if goal:
            if 'career change' in goal.lower():
                if any(keyword in course_name_lower for keyword in ['full stack', 'data science', 'cyber']):
                    score += 10
                else:
                    score += 8
            elif 'skill upgrade' in goal.lower() or 'promotion' in goal.lower():
                score += 10
            elif 'exploring' in goal.lower() or 'interest' in goal.lower():
                if 'beginner' in course.get('suitable_for', '').lower():
                    score += 10
                else:
                    score += 7
            else:
                score += 8
        
        return min(score, 100)
    
    def get_reasoning(self, interest, career_role, experience, goal):
        """Generate human-readable reasoning"""
        reasons = []
        
        if interest and 'unsure' not in interest.lower():
            reasons.append(f"✓ Matches your interest in {interest}")
        
        if career_role and 'unsure' not in career_role.lower() and career_role != 'general':
            reasons.append(f"✓ Aligns with your goal to become a {career_role}")
        
        if experience:
            exp_mapping = {
                'beginner': 'complete beginners',
                'basic': 'learners with foundational knowledge',
                'intermediate': 'professionals with practical experience',
                'advanced': 'experienced professionals'
            }
            level_text = exp_mapping.get(experience, 'your experience level')
            reasons.append(f"✓ Designed for {level_text}")
        
        if goal:
            goal_mapping = {
                'career change': 'career changers with placement support',
                'skill upgrade': 'professionals upgrading skills',
                'personal interest': 'learners exploring new fields',
                'career advancement': 'professionals aiming for growth'
            }
            goal_text = goal_mapping.get(goal, 'your learning goals')
            reasons.append(f"✓ Perfect for {goal_text}")
        
        if not reasons:
            return "Excellent match based on your profile"
        
        return '<br>'.join(reasons)


class ActionShowDetailedRecommendation(Action):
    """Show FULL course details including career paths and salary"""
    
    def name(self) -> Text:
        return "action_show_detailed_recommendation"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        recommended_course = tracker.get_slot("recommended_course")
        
        if not recommended_course:
            dispatcher.utter_message(text="Let me help you find the right course first!")
            return []
        
        # Get course details from CSV
        csv_path = os.path.join(os.path.dirname(__file__), "course_data.csv")
        
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['course_name'].lower() == recommended_course.lower():
                    
                    # Parse skills
                    skills_list = row.get('key_skills', '').split('|')
                    skills_formatted = '<br>• '.join(skills_list)
                    
                    message = (
                        f"<b>📚 Complete Course Details</b><br>"
                        f"<b>{row['course_name']}</b><br><br>"
                        f"<b>📖 Description:</b><br>"
                        f"{row['description']}<br><br>"
                        f"<b>⏱️ Duration:</b> {row['duration']}<br>"
                        f"<b>💰 Fees:</b> {row['fees']}<br>"
                        f"<b>📊 Suitable For:</b> {row['suitable_for'].replace('|', ', ')}<br><br>"
                        f"<b>🎯 Key Skills Covered:</b><br>• {skills_formatted}<br><br>"
                        f"<b>✨ What Makes This Course Special:</b><br>"
                        f"• 100% Placement Assistance for eligible candidates<br>"
                        f"• Scholarships and Cash-backs for meritorious students<br>"
                        f"• 3-6 month access to LinkedIn Learning<br>"
                        f"• Comprehensive Employability Skills training<br>"
                        f"• Expert sessions by Industry Professionals<br>"
                        f"• Online and Offline sessions available<br><br>"
                        f"Ready to start your journey?"
                    )
                    
                    dispatcher.utter_message(
                        text=message,
                        buttons=[
                            {"title": "💼 Career & Salary Info", "payload": "/request_career_info"},
                            {"title": "📞 Contact Admissions", "payload": "/ask_contact"},
                            {"title": "📊 Compare Courses", "payload": "/view_courses"}
                        ]
                    )
                    return []
        
        dispatcher.utter_message(text="Course details not found.")
        return []


class ActionShowCareerInfo(Action):
    """NEW: Separate action for career paths and salary information"""
    
    def name(self) -> Text:
        return "action_show_career_info"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        recommended_course = tracker.get_slot("recommended_course")
        
        if not recommended_course:
            dispatcher.utter_message(text="Let me help you find the right course first!")
            return []
        
        # Get course details from CSV
        csv_path = os.path.join(os.path.dirname(__file__), "course_data.csv")
        
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['course_name'].lower() == recommended_course.lower():
                    
                    # Parse career paths
                    careers_list = row.get('career_paths', '').split('|')
                    careers_formatted = '<br>• '.join(careers_list)
                    
                    # Parse salary ranges
                    salary_list = row.get('job_roles_salary', '').split('|')
                    salary_formatted = '<br>• '.join(salary_list)
                    
                    message = (
                        f"<b>💼 Career Opportunities & Salary Information</b><br>"
                        f"<b>{row['course_name']}</b><br><br>"
                        f"<b>🎯 Career Paths:</b><br>• {careers_formatted}<br><br>"
                        f"<b>💵 Expected Salary Ranges:</b><br>• {salary_formatted}<br><br>"
                        f"<b>📈 Career Growth:</b><br>"
                        f"• Entry Level: Start as Junior/Associate roles<br>"
                        f"• Mid Level (2-4 years): Senior positions<br>"
                        f"• Advanced (5+ years): Lead/Architect roles<br><br>"
                        f"<b>🌟 Industry Demand:</b><br>"
                        f"High demand across IT, Banking, Healthcare, E-commerce, "
                        f"Consulting, and Government sectors.<br><br>"
                        f"💡 With ICTAK's 100% placement assistance, you'll have support "
                        f"throughout your job search!"
                    )
                    
                    dispatcher.utter_message(
                        text=message,
                        buttons=[
                            {"title": "📖 View Full Course Details", "payload": "/request_more_info"},
                            {"title": "📞 Talk to Career Counselor", "payload": "/ask_contact"},
                            {"title": "✅ I'm Interested", "payload": "/ask_contact"}
                        ]
                    )
                    return []
        
        dispatcher.utter_message(text="Career information not found.")
        return []