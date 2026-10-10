class CareerGuidanceService:
    """
    Rule-based, transparent AI Career Guidance & Skill Mapping Service.
    Compares student skills against industry job profiles to build customized learning roadmaps.
    """

    ROLE_PROFILES = {
        'Software Developer': {
            'core_skills': ['Python', 'Java', 'Data Structures', 'Algorithms', 'Git', 'SQL', 'Object Oriented Programming', 'System Design Basics'],
            'description': 'Designs, builds, tests, and maintains full-lifecycle software applications and core algorithms.',
            'industry_demand': 'High',
            'average_readiness_benchmark': 70.0,
            'roadmap': [
                {'stage': 'Phase 1: Foundations', 'topics': ['Master Data Structures (Arrays, Trees, Graphs)', 'Object-Oriented Design in Python/Java'], 'duration_weeks': 4},
                {'stage': 'Phase 2: Core Engineering', 'topics': ['Database Design & SQL Optimization', 'Version Control with Git & Unit Testing'], 'duration_weeks': 4},
                {'stage': 'Phase 3: System & Algorithms', 'topics': ['Dynamic Programming & Graph Algorithms', 'Basic Microservices & REST APIs'], 'duration_weeks': 4},
                {'stage': 'Phase 4: Capstone & Portfolio', 'topics': ['End-to-End Full Stack App Deployment', 'Mock Technical Problem Solving'], 'duration_weeks': 2}
            ],
            'recommended_projects': [
                'Distributed Task Queue & Scheduler',
                'E-commerce Inventory & Payment Gateway API',
                'Real-time Collaborative Whiteboard'
            ]
        },
        'Frontend Developer': {
            'core_skills': ['HTML5', 'CSS3', 'JavaScript', 'React', 'TypeScript', 'Responsive Design', 'Web Accessibility (a11y)', 'REST API Integration'],
            'description': 'Builds rich, accessible, responsive user interfaces and interactive web client experiences.',
            'industry_demand': 'High',
            'average_readiness_benchmark': 72.0,
            'roadmap': [
                {'stage': 'Phase 1: Modern Web UI', 'topics': ['Semantic HTML5, Modern CSS Grid/Flexbox', 'JavaScript ES6+ asynchronous programming'], 'duration_weeks': 3},
                {'stage': 'Phase 2: Component Architecture', 'topics': ['React hooks, state management (Redux/Zustand)', 'TypeScript integration'], 'duration_weeks': 4},
                {'stage': 'Phase 3: Performance & APIs', 'topics': ['API Caching, Web Vitals optimization', 'Tailwind/CSS Modules architecture'], 'duration_weeks': 3},
                {'stage': 'Phase 4: Polish & Build', 'topics': ['Accessibility auditing, End-to-End Cypress testing', 'Production build deployment with CI/CD'], 'duration_weeks': 2}
            ],
            'recommended_projects': [
                'Interactive Data Analytics Dashboard',
                'Kanban Project Management Board with Drag & Drop',
                'E-learning Interactive Course Player'
            ]
        },
        'Backend Developer': {
            'core_skills': ['Python', 'Node.js', 'PostgreSQL', 'REST APIs', 'Docker', 'Redis Caching', 'Authentication & JWT', 'Microservices'],
            'description': 'Architects resilient server-side services, database schemas, scalable APIs, and caching layers.',
            'industry_demand': 'Very High',
            'average_readiness_benchmark': 75.0,
            'roadmap': [
                {'stage': 'Phase 1: Server & Database Fundamentals', 'topics': ['RESTful API principles (Flask/Express)', 'Relational database schema modeling & indexing'], 'duration_weeks': 4},
                {'stage': 'Phase 2: Security & Session Management', 'topics': ['JWT, OAuth2, Role-Based Access Control', 'Input validation and rate-limiting'], 'duration_weeks': 3},
                {'stage': 'Phase 3: Scaling & Caching', 'topics': ['Redis in-memory caching', 'Message queues (RabbitMQ/Celery)', 'Containerization with Docker'], 'duration_weeks': 4},
                {'stage': 'Phase 4: Resiliency', 'topics': ['Load balancing, database sharding fundamentals', 'Observability & structured logging'], 'duration_weeks': 3}
            ],
            'recommended_projects': [
                'High-Concurrency Ticket Booking Engine',
                'Secure Multi-Tenant Auth Service with Webhooks',
                'Distributed File Storage and Metadata Indexer'
            ]
        },
        'Data Analyst': {
            'core_skills': ['Python', 'SQL', 'Pandas', 'NumPy', 'Data Visualization', 'PowerBI/Tableau', 'Statistics & Probability', 'Excel Advanced'],
            'description': 'Extracts insights from structured data, designs executive reports, and identifies key operational trends.',
            'industry_demand': 'High',
            'average_readiness_benchmark': 68.0,
            'roadmap': [
                {'stage': 'Phase 1: Querying & Wrangling', 'topics': ['Advanced SQL (Window functions, CTEs)', 'Data cleaning with Pandas & NumPy'], 'duration_weeks': 4},
                {'stage': 'Phase 2: Statistical Analysis', 'topics': ['Descriptive & inferential statistics', 'Hypothesis testing and A/B test analysis'], 'duration_weeks': 3},
                {'stage': 'Phase 3: BI Dashboards', 'topics': ['PowerBI / Tableau dashboard storytelling', 'KPI metric modeling and automated reports'], 'duration_weeks': 3},
                {'stage': 'Phase 4: Business Insights', 'topics': ['Exploratory Data Analysis case studies', 'Executive presentation synthesis'], 'duration_weeks': 2}
            ],
            'recommended_projects': [
                'Student Retention & Graduation Predictive EDA',
                'E-commerce Customer Churn & Cohort Analysis',
                'Healthcare Resource Utilization Executive Dashboard'
            ]
        },
        'QA Engineer': {
            'core_skills': ['Manual Testing', 'Selenium/Playwright', 'API Testing (Postman)', 'Python/Java', 'Test Case Design', 'CI/CD Pipelines', 'Defect Tracking (Jira)', 'Performance Testing (JMeter)'],
            'description': 'Ensures software quality, reliability, and security through automated test suites and validation pipelines.',
            'industry_demand': 'Moderate',
            'average_readiness_benchmark': 65.0,
            'roadmap': [
                {'stage': 'Phase 1: Testing Fundamentals', 'topics': ['SDLC & STLC principles', 'Test case writing, boundary value analysis, Jira defect life-cycle'], 'duration_weeks': 3},
                {'stage': 'Phase 2: Automated Testing', 'topics': ['Selenium/Playwright with Python/Java', 'Page Object Model test design pattern'], 'duration_weeks': 4},
                {'stage': 'Phase 3: API & Non-Functional Testing', 'topics': ['REST API automation with Pytest/Newman', 'Load testing with JMeter/Locust'], 'duration_weeks': 3},
                {'stage': 'Phase 4: Integration', 'topics': ['GitHub Actions CI/CD test automation pipelines', 'Security testing fundamentals (OWASP)'], 'duration_weeks': 2}
            ],
            'recommended_projects': [
                'Automated E2E Testing Suite for SaaS Web App',
                'REST API Automated Regression Test Framework',
                'Performance Benchmark & Stress Test Report'
            ]
        },
        'Cloud or IT Support Associate': {
            'core_skills': ['Linux Fundamentals', 'Networking (TCP/IP, DNS)', 'AWS Basics', 'Bash Scripting', 'Virtualization', 'Troubleshooting', 'Identity & Access Management (IAM)', 'Security Basics'],
            'description': 'Maintains cloud infrastructure, provisions networks, troubleshoots servers, and supports reliable systems.',
            'industry_demand': 'High',
            'average_readiness_benchmark': 65.0,
            'roadmap': [
                {'stage': 'Phase 1: Linux & Networking', 'topics': ['Linux shell navigation, user permissions, systemctl', 'TCP/IP, subnetting, DNS, SSL/TLS certificates'], 'duration_weeks': 3},
                {'stage': 'Phase 2: Cloud Computing Core', 'topics': ['AWS EC2, S3, VPC networking, IAM security policies', 'CloudWatch monitoring and alerting'], 'duration_weeks': 4},
                {'stage': 'Phase 3: Automation & Scripting', 'topics': ['Bash scripting for server maintenance', 'Infrastructure as Code (Terraform basics)'], 'duration_weeks': 3},
                {'stage': 'Phase 4: Operations & Incident Response', 'topics': ['Backup recovery plans, audit log review', 'Service desk ticketing and customer support simulation'], 'duration_weeks': 2}
            ],
            'recommended_projects': [
                'Highly Available Multi-AZ AWS Web Server Architecture',
                'Automated Linux Server Health & Log Backup Daemon',
                'Enterprise Zero-Trust IAM & Security Group Configuration'
            ]
        }
    }

    @classmethod
    def get_role_list(cls):
        return list(cls.ROLE_PROFILES.keys())

    @classmethod
    def analyze_career_path(cls, user_skills, target_role=None, proficiency='Intermediate', preferred_areas=None):
        """
        Analyzes skill gaps, matches roles, and returns an actionable learning plan.
        """
        if isinstance(user_skills, str):
            user_skills = [s.strip() for s in user_skills.replace(';', ',').split(',') if s.strip()]

        cleaned_user_skills = {s.lower() for s in user_skills}
        role_matches = []

        for role_name, details in cls.ROLE_PROFILES.items():
            core = details['core_skills']
            matched = [s for s in core if s.lower() in cleaned_user_skills or any(s.lower() in u for u in cleaned_user_skills)]
            missing = [s for s in core if s not in matched]

            match_pct = round((len(matched) / len(core) * 100), 1) if core else 0

            role_matches.append({
                'role': role_name,
                'description': details['description'],
                'industry_demand': details['industry_demand'],
                'match_percentage': match_pct,
                'matching_skills': matched,
                'missing_skills': missing,
                'total_required_skills': len(core)
            })

        # Sort matches descending
        role_matches.sort(key=lambda x: x['match_percentage'], reverse=True)

        selected_role = target_role if target_role in cls.ROLE_PROFILES else role_matches[0]['role']
        selected_details = cls.ROLE_PROFILES[selected_role]

        core = selected_details['core_skills']
        target_matched = [s for s in core if s.lower() in cleaned_user_skills or any(s.lower() in u for u in cleaned_user_skills)]
        target_missing = [s for s in core if s not in target_matched]
        target_pct = round((len(target_matched) / len(core) * 100), 1) if core else 0

        explanation = (
            f"Based on your {len(user_skills)} reported skills, you currently fulfill {len(target_matched)} of {len(core)} "
            f"core competencies ({target_pct}%) for '{selected_role}'. Bridging the remaining {len(target_missing)} skills "
            f"will align your profile with standard entry-level hiring criteria."
        )

        return {
            'target_role': selected_role,
            'match_percentage': target_pct,
            'matching_skills': target_matched,
            'missing_skills': target_missing,
            'explanation': explanation,
            'roadmap': selected_details['roadmap'],
            'recommended_projects': selected_details['recommended_projects'],
            'all_role_matches': role_matches
        }
