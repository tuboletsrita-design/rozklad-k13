import json
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Розклад групи")


def get_current_week_type() -> str:
    """Визначає парність поточного тижня."""
    week_number = datetime.now().isocalendar()[1]
    return "even" if week_number % 2 != 0 else "odd"


def load_schedule():
    """Завантажує розклад із JSON-файлу."""
    try:
        with open("schedule.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


@app.get("/api/schedule")
def get_full_schedule(week: str = None):
    raw_schedule = load_schedule()
    current_week = week or get_current_week_type()

    filtered_schedule = {}
    for day, lessons in raw_schedule.items():
        if day == "saturday":
            continue
        day_lessons = [
            lesson
            for lesson in lessons
            if lesson.get("week_type") in ("all", current_week)
        ]
        filtered_schedule[day] = day_lessons

    now = datetime.now()
    days_map = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "monday",
        6: "monday",
    }
    today_key = days_map.get(now.weekday(), "monday")

    return {
        "current_week_type": current_week,
        "week_number": now.isocalendar()[1],
        "today": today_key,
        "current_time": now.strftime("%H:%M"),
        "schedule": filtered_schedule,
    }


@app.get("/get-link")
def get_current_lesson_link():
    """Повертає посилання на пару, яка йде просто зараз."""
    schedule_data = get_full_schedule()
    today = schedule_data["today"]
    today_lessons = schedule_data["schedule"].get(today, [])

    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute

    for lesson in today_lessons:
        try:
            start_str, end_str = lesson["time"].split(" - ")
            start_h, start_m = map(int, start_str.split(":"))
            end_h, end_m = map(int, end_str.split(":"))

            start_min = start_h * 60 + start_m
            end_min = end_h * 60 + end_m

            if start_min <= current_minutes <= end_min:
                if lesson.get("link"):
                    return {
                        "status": "live",
                        "subject": lesson["subject"],
                        "link": lesson["link"],
                    }
                return {
                    "status": "live_no_link",
                    "subject": lesson["subject"],
                    "message": "Пара йде зараз, але посилання ще не додано",
                }
        except Exception:
            continue

    for lesson in today_lessons:
        if lesson.get("link"):
            return {
                "status": "next_available",
                "subject": lesson["subject"],
                "time": lesson["time"],
                "link": lesson["link"],
            }

    return {
        "status": "no_links",
        "message": "На сьогодні немає доступних посилань",
    }


@app.get("/", response_class=HTMLResponse)
def render_ui():
    current_week = get_current_week_type()
    week_label = "ПАРНИЙ" if current_week == "even" else "НЕПАРНИЙ"

    return f"""
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Розклад групи 🥥</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🥥</text></svg>">
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #09090b;
                --card-bg: #121215;
                --card-border: rgba(255, 255, 255, 0.08);
                --btn-bg: #18181b;
                --text-main: #f4f4f5;
                --text-muted: #a1a1aa;
                --accent-blue: #3b82f6;
                --accent-purple: #a855f7;
                --accent-cyan: #06b6d4;
                --accent-pink: #ec4899;
                --badge-bg: rgba(255, 255, 255, 0.06);
                --iframe-filter: invert(0.9) hue-rotate(180deg) contrast(0.9);
            }}

            [data-theme="light"] {{
                --bg: #f1f5f9;
                --card-bg: #ffffff;
                --card-border: rgba(0, 0, 0, 0.08);
                --btn-bg: #e2e8f0;
                --text-main: #0f172a;
                --text-muted: #64748b;
                --badge-bg: rgba(0, 0, 0, 0.05);
                --iframe-filter: none;
            }}

            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}

            body {{
                font-family: 'Plus Jakarta Sans', sans-serif;
                background-color: var(--bg);
                color: var(--text-main);
                padding: 20px 15px 60px;
                min-height: 100vh;
                position: relative;
                overflow-x: hidden;
                transition: background-color 0.3s ease, color 0.3s ease;
            }}

            .bg-coconut {{
                position: fixed;
                font-size: 5.5rem;
                opacity: 0.18;
                user-select: none;
                pointer-events: none;
                z-index: 0;
                animation: float 10s ease-in-out infinite alternate;
            }}

            .c1 {{ top: 5%; left: 3%; transform: rotate(-15deg); }}
            .c2 {{ top: 15%; right: 5%; transform: rotate(20deg); animation-delay: -2s; }}
            .c3 {{ top: 45%; left: 2%; transform: rotate(-10deg); animation-delay: -5s; }}
            .c4 {{ top: 55%; right: 3%; transform: rotate(25deg); animation-delay: -3s; }}
            .c5 {{ bottom: 12%; left: 6%; transform: rotate(15deg); animation-delay: -7s; }}
            .c6 {{ bottom: 8%; right: 7%; transform: rotate(-20deg); animation-delay: -4s; }}
            .c7 {{ top: 30%; left: 48%; transform: rotate(12deg); font-size: 4rem; animation-delay: -6s; }}
            .c8 {{ bottom: 35%; right: 45%; transform: rotate(-18deg); font-size: 4.5rem; animation-delay: -1s; }}

            @keyframes float {{
                0% {{ transform: translateY(0) rotate(0deg); }}
                100% {{ transform: translateY(-20px) rotate(12deg); }}
            }}

            .container {{
                max-width: 1200px;
                margin: 0 auto;
                position: relative;
                z-index: 1;
            }}

            header {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 10px;
                margin-bottom: 20px;
                position: relative;
            }}

            .theme-toggle {{
                position: absolute;
                top: 0;
                right: 0;
                background: var(--btn-bg);
                border: 1px solid var(--card-border);
                color: var(--text-main);
                font-size: 1.2rem;
                padding: 8px 12px;
                border-radius: 50%;
                cursor: pointer;
                transition: all 0.2s ease;
            }}

            .theme-toggle:hover {{
                transform: scale(1.1);
            }}

            h1 {{
                font-size: 2rem;
                font-weight: 800;
                display: flex;
                align-items: center;
                gap: 10px;
            }}

            .week-info {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                padding: 6px 16px;
                border-radius: 20px;
                font-size: 0.85rem;
                color: var(--text-muted);
            }}

            .week-info span {{
                color: var(--accent-blue);
                font-weight: 700;
            }}

            .main-nav {{
                display: flex;
                justify-content: center;
                gap: 10px;
                margin-bottom: 25px;
                flex-wrap: wrap;
            }}

            .nav-btn {{
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                color: var(--text-muted);
                padding: 10px 20px;
                border-radius: 14px;
                font-family: inherit;
                font-weight: 700;
                font-size: 0.95rem;
                cursor: pointer;
                transition: all 0.25s ease;
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            .nav-btn:hover {{
                border-color: var(--accent-blue);
                color: var(--text-main);
            }}

            .nav-btn.active {{
                background: var(--accent-purple);
                color: #ffffff;
                border-color: transparent;
                box-shadow: 0 4px 16px rgba(168, 85, 247, 0.35);
            }}

            .controls-wrapper {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 12px;
                margin-bottom: 25px;
            }}

            .days-filter {{
                display: flex;
                justify-content: center;
                gap: 8px;
                flex-wrap: wrap;
            }}

            .day-btn {{
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                color: var(--text-muted);
                padding: 8px 16px;
                border-radius: 12px;
                font-family: inherit;
                font-weight: 700;
                font-size: 0.88rem;
                cursor: pointer;
                transition: all 0.2s ease;
            }}

            .day-btn:hover {{
                border-color: var(--accent-blue);
                color: var(--text-main);
            }}

            .day-btn.active {{
                background: var(--accent-blue);
                color: #ffffff;
                border-color: transparent;
                box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35);
            }}

            .subgroup-filter, .teacher-filter-group {{
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                justify-content: center;
                align-items: center;
            }}

            .filter-label {{
                font-size: 0.8rem;
                font-weight: 700;
                color: var(--text-muted);
                margin-right: 4px;
            }}

            .filter-btn {{
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                color: var(--text-muted);
                padding: 6px 14px;
                border-radius: 10px;
                font-family: inherit;
                font-size: 0.82rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }}

            .filter-btn:hover {{
                color: var(--text-main);
                border-color: var(--accent-purple);
            }}

            .filter-btn.active {{
                background: var(--accent-purple);
                color: #ffffff;
                border-color: transparent;
            }}

            .ag-btn.active {{
                background: var(--accent-cyan);
                color: #000000;
                font-weight: 800;
                border-color: transparent;
            }}

            .eng-btn.active {{
                background: var(--accent-pink);
                color: #ffffff;
                font-weight: 800;
                border-color: transparent;
            }}

            .kanban-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 15px;
                align-items: start;
            }}

            .kanban-column {{
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 16px;
                padding: 14px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}

            .column-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding-bottom: 10px;
                border-bottom: 1px solid var(--card-border);
                font-weight: 800;
                font-size: 1.05rem;
            }}

            .day-dot {{
                width: 10px;
                height: 10px;
                border-radius: 50%;
                display: inline-block;
            }}

            .dot-mon {{ background: #3b82f6; }}
            .dot-tue {{ background: #10b981; }}
            .dot-wed {{ background: #f59e0b; }}
            .dot-thu {{ background: #8b5cf6; }}
            .dot-fri {{ background: #ec4899; }}

            .column-header .today-badge {{
                background: var(--accent-blue);
                color: #fff;
                font-size: 0.68rem;
                padding: 2px 8px;
                border-radius: 12px;
                font-weight: 700;
            }}

            .kanban-card {{
                background: var(--btn-bg);
                border: 1px solid var(--card-border);
                border-radius: 12px;
                padding: 12px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                position: relative;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }}

            .kanban-card:hover {{
                transform: translateY(-2px);
            }}

            .kanban-card.is-live {{
                border-color: #ec4899;
                box-shadow: 0 0 20px rgba(236, 72, 153, 0.35);
                animation: pulse-live 2s infinite alternate;
            }}

            @keyframes pulse-live {{
                0% {{ border-color: rgba(236, 72, 153, 0.5); }}
                100% {{ border-color: rgba(236, 72, 153, 1); }}
            }}

            .live-badge-bar {{
                background: linear-gradient(90deg, #ec4899, #a855f7);
                color: #ffffff;
                font-size: 0.72rem;
                font-weight: 800;
                padding: 4px 8px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                gap: 6px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            .timer-box {{
                background: rgba(236, 72, 153, 0.15);
                border: 1px solid rgba(236, 72, 153, 0.4);
                color: #f472b6;
                padding: 6px 10px;
                border-radius: 8px;
                font-size: 0.8rem;
                font-weight: 700;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
            }}

            .card-top {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 6px;
            }}

            .card-type-group {{
                display: flex;
                align-items: center;
                gap: 6px;
            }}

            .lesson-num-badge {{
                font-size: 0.68rem;
                font-weight: 800;
                background: var(--accent-blue);
                color: #ffffff;
                padding: 2px 6px;
                border-radius: 6px;
            }}

            .card-type {{
                font-size: 0.68rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: var(--text-muted);
            }}

            .card-subgroup {{
                font-size: 0.68rem;
                font-weight: 800;
                background: var(--badge-bg);
                padding: 2px 6px;
                border-radius: 6px;
            }}

            .card-title {{
                font-size: 0.95rem;
                font-weight: 700;
                line-height: 1.25;
            }}

            .card-teacher {{
                font-size: 0.78rem;
                color: var(--text-muted);
            }}

            .card-time {{
                font-size: 0.75rem;
                font-weight: 700;
                color: var(--accent-cyan);
            }}

            .card-actions {{
                display: flex;
                gap: 6px;
                margin-top: 4px;
            }}

            .btn-zoom {{
                background: #2563eb;
                color: #ffffff;
                text-decoration: none;
                font-size: 0.75rem;
                font-weight: 700;
                padding: 5px 12px;
                border-radius: 8px;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }}

            .btn-meet {{
                background: #059669;
                color: #ffffff;
                text-decoration: none;
                font-size: 0.75rem;
                font-weight: 700;
                padding: 5px 12px;
                border-radius: 8px;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }}

            .iframe-container {{
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 20px;
                padding: 10px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                overflow: hidden;
            }}

            .iframe-container iframe {{
                width: 100%;
                height: 78vh;
                border: none;
                border-radius: 12px;
                background: #ffffff;
                filter: var(--iframe-filter);
                transition: filter 0.3s ease;
            }}

            .single-day-wrapper {{
                max-width: 650px;
                margin: 0 auto;
            }}

            @media (max-width: 768px) {{
                .kanban-grid {{
                    grid-template-columns: 1fr;
                }}
                .iframe-container iframe {{
                    height: 68vh;
                }}
            }}
        </style>
    </head>
    <body>

        <div class="bg-coconut c1">🥥</div>
        <div class="bg-coconut c2">🥥</div>
        <div class="bg-coconut c3">🥥</div>
        <div class="bg-coconut c4">🥥</div>
        <div class="bg-coconut c5">🥥</div>
        <div class="bg-coconut c6">🥥</div>
        <div class="bg-coconut c7">🥥</div>
        <div class="bg-coconut c8">🥥</div>

        <div class="container">
            <header>
                <button class="theme-toggle" onclick="toggleTheme()" id="theme-btn">🌙</button>
                <h1>🥥 Розклад Занять 🥥</h1>
                <div class="week-info">Тиждень: <span>{week_label}</span></div>
            </header>

            <div class="main-nav">
                <button class="nav-btn active" onclick="switchSection('schedule')" id="nav-schedule">
                    📅 Розклад
                </button>
                <button class="nav-btn" onclick="switchSection('recordings')" id="nav-recordings">
                    🎥 Записи лекцій/практик
                </button>
                <button class="nav-btn" onclick="switchSection('homework')" id="nav-homework">
                    📝 ДЗ
                </button>
            </div>

            <div id="section-schedule">
                <div class="controls-wrapper">
                    <!-- ФІЛЬТР ДНІВ (БЕЗ СУБОТИ) -->
                    <div class="days-filter" id="days-filter-container"></div>

                    <!-- ФІЛЬТР ПІДГРУПИ -->
                    <div class="subgroup-filter">
                        <span class="filter-label">Підгрупа:</span>
                        <button class="filter-btn sub-btn active" onclick="setSubgroupFilter('all')">Всі</button>
                        <button class="filter-btn sub-btn" onclick="setSubgroupFilter('П1')">1 ПГ (П1)</button>
                        <button class="filter-btn sub-btn" onclick="setSubgroupFilter('П2')">2 ПГ (П2)</button>
                    </div>

                    <!-- ФІЛЬТР ВИКЛАДАЧІВ АГ -->
                    <div class="teacher-filter-group">
                        <span class="filter-label">Викладач АГ:</span>
                        <button class="filter-btn ag-btn active" onclick="setAgTeacherFilter('all')">Всі</button>
                        <button class="filter-btn ag-btn" onclick="setAgTeacherFilter('Браганець')">Браганець</button>
                        <button class="filter-btn ag-btn" onclick="setAgTeacherFilter('Костогриз')">Костогриз</button>
                    </div>

                    <!-- ФІЛЬТР ВИКЛАДАЧІВ АНГЛІЙСЬКОЇ -->
                    <div class="teacher-filter-group">
                        <span class="filter-label">Англійська:</span>
                        <button class="filter-btn eng-btn active" onclick="setEngTeacherFilter('all')">Всі</button>
                        <button class="filter-btn eng-btn" onclick="setEngTeacherFilter('Лисенко')">Лисенко</button>
                        <button class="filter-btn eng-btn" onclick="setEngTeacherFilter('Степанечко')">Степанечко</button>
                    </div>
                </div>

                <div id="schedule-container">Завантаження розкладу...</div>
            </div>

            <div id="section-recordings" style="display: none;">
                <div class="iframe-container">
                    <iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vTDpDnWf26AWuZiVqtpxx4wCeYnak_z1YjyiXWFs8-NzlutOP9eQQNCrED97hCaHb-Y6CW0Ur30N-1Q/pubhtml?widget=true&amp;headers=false"></iframe>
                </div>
            </div>

            <div id="section-homework" style="display: none;">
                <div class="iframe-container">
                    <iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vT3jeYJV7pxlUEGO4uNDNeYFkBoOR7w1-lCDMymQ7CfLoH5dtEI7nLpGk_US29zc_KUSDiPzkr54Xu9/pubhtml?widget=true&amp;headers=false"></iframe>
                </div>
            </div>

        </div>

        <script>
            let currentSection = 'schedule';
            let currentSubgroup = 'all';
            let currentAgTeacher = 'all';
            let currentEngTeacher = 'all';
            let selectedDay = 'today'; 
            let scheduleData = null;

            // ДНІ БЕЗ СУБОТИ
            const daysMapUa = {{
                monday: 'Пн', tuesday: 'Вт', wednesday: 'Ср',
                thursday: 'Чт', friday: "Пт"
            }};

            const daysFullUa = {{
                monday: 'Понеділок', tuesday: 'Вівторок', wednesday: 'Середа',
                thursday: 'Четвер', friday: "П'ятниця"
            }};

            const dayDotClasses = {{
                monday: 'dot-mon', tuesday: 'dot-tue', wednesday: 'dot-wed',
                thursday: 'dot-thu', friday: 'dot-fri'
            }};

            function switchSection(section) {{
                currentSection = section;

                document.getElementById('section-schedule').style.display = section === 'schedule' ? 'block' : 'none';
                document.getElementById('section-recordings').style.display = section === 'recordings' ? 'block' : 'none';
                document.getElementById('section-homework').style.display = section === 'homework' ? 'block' : 'none';

                document.querySelectorAll('.main-nav .nav-btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById(`nav-${{section}}`).classList.add('active');
            }}

            function toggleTheme() {{
                const currentTheme = document.body.getAttribute('data-theme');
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                document.body.setAttribute('data-theme', newTheme);
                document.getElementById('theme-btn').innerText = newTheme === 'light' ? '☀️' : '🌙';
                localStorage.setItem('theme', newTheme);
            }}

            if (localStorage.getItem('theme') === 'light') {{
                toggleTheme();
            }}

            function setDayFilter(day) {{
                selectedDay = day;
                renderDaysButtons();
                renderSchedule();
            }}

            function setSubgroupFilter(filter) {{
                currentSubgroup = filter;
                document.querySelectorAll('.subgroup-filter .sub-btn').forEach(btn => {{
                    btn.classList.toggle('active', btn.getAttribute('onclick').includes(`'${{filter}}'`));
                }});
                renderSchedule();
            }}

            function setAgTeacherFilter(teacher) {{
                currentAgTeacher = teacher;
                document.querySelectorAll('.ag-btn').forEach(btn => {{
                    btn.classList.toggle('active', btn.getAttribute('onclick').includes(`'${{teacher}}'`));
                }});
                renderSchedule();
            }}

            function setEngTeacherFilter(teacher) {{
                currentEngTeacher = teacher;
                document.querySelectorAll('.eng-btn').forEach(btn => {{
                    btn.classList.toggle('active', btn.getAttribute('onclick').includes(`'${{teacher}}'`));
                }});
                renderSchedule();
            }}

            function renderDaysButtons() {{
                if (!scheduleData) return;

                const container = document.getElementById('days-filter-container');

                let html = `
                    <button class="day-btn ${{selectedDay === 'today' ? 'active' : ''}}" onclick="setDayFilter('today')">
                        ✨ Сьогодні
                    </button>
                `;

                for (const [dayKey, dayShort] of Object.entries(daysMapUa)) {{
                    const isActive = (selectedDay === dayKey);

                    html += `
                        <button class="day-btn ${{isActive ? 'active' : ''}}" onclick="setDayFilter('${{dayKey}}')">
                            ${{dayShort}}
                        </button>
                    `;
                }}

                html += `
                    <button class="day-btn ${{selectedDay === 'all' ? 'active' : ''}}" onclick="setDayFilter('all')">
                        📊 Всі дні
                    </button>
                `;

                container.innerHTML = html;
            }}

            function getLessonNumber(timeStr) {{
                if (!timeStr) return '';
                const startStr = timeStr.split(' - ')[0].trim();

                if (startStr.startsWith('08:') || startStr.startsWith('8:')) return '1 пара';
                if (startStr.startsWith('10:')) return '2 пара';
                if (startStr.startsWith('12:')) return '3 пара';
                if (startStr.startsWith('14:')) return '4 пара';

                return '';
            }}

            function getLessonStatus(timeStr, isToday) {{
                if (!isToday) return {{ isLive: false, timeLeftText: '' }};

                try {{
                    const [startStr, endStr] = timeStr.split(' - ');
                    const [startH, startM] = startStr.split(':').map(Number);
                    const [endH, endM] = endStr.split(':').map(Number);

                    const now = new Date();
                    const nowSec = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
                    const startSec = startH * 3600 + startM * 60;
                    const endSec = endH * 3600 + endM * 60;

                    if (nowSec >= startSec && nowSec <= endSec) {{
                        const diffSec = endSec - nowSec;
                        const minLeft = Math.floor(diffSec / 60);
                        const secLeft = diffSec % 60;
                        return {{
                            isLive: true,
                            timeLeftText: `⏳ До кінця пари: ${{minLeft}} хв ${{secLeft < 10 ? '0' : ''}}${{secLeft}} сек`
                        }};
                    }}
                }} catch (e) {{
                    return {{ isLive: false, timeLeftText: '' }};
                }}

                return {{ isLive: false, timeLeftText: '' }};
            }}

            function filterLessons(lessons) {{
                return lessons.filter(l => {{
                    const subjectName = (l.subject || '').toLowerCase();
                    const teacherName = (l.teacher || '').toLowerCase();

                    if (currentSubgroup === 'П1' && l.subject.includes('(П2)')) return false;
                    if (currentSubgroup === 'П2' && l.subject.includes('(П1)')) return false;

                    if (currentAgTeacher !== 'all' && subjectName.includes('алгебра')) {{
                        if (!teacherName.includes(currentAgTeacher.toLowerCase())) return false;
                    }}

                    if (currentEngTeacher !== 'all' && (subjectName.includes('іноземна') || subjectName.includes('англ'))) {{
                        if (!teacherName.includes(currentEngTeacher.toLowerCase())) return false;
                    }}

                    return true;
                }});
            }}

            function renderSchedule() {{
                if (!scheduleData) return;

                const container = document.getElementById('schedule-container');
                container.innerHTML = '';

                if (selectedDay === 'all') {{
                    let gridHtml = '<div class="kanban-grid">';

                    for (const [day, lessons] of Object.entries(scheduleData.schedule)) {{
                        if (day === 'saturday') continue;
                        const isToday = (day === scheduleData.today);
                        const filtered = filterLessons(lessons);

                        let cardsHtml = filtered.map(l => {{
                            const status = getLessonStatus(l.time, isToday);
                            const lessonNum = getLessonNumber(l.time);
                            const isZoom = l.link && l.link.includes('zoom');
                            const btnClass = isZoom ? 'btn-zoom' : 'btn-meet';
                            const btnText = isZoom ? '🎥 Zoom' : '🟢 Meet';

                            let subGroupBadge = '';
                            if (l.subject.includes('(П1)')) subGroupBadge = '<span class="card-subgroup">1 ПГ</span>';
                            if (l.subject.includes('(П2)')) subGroupBadge = '<span class="card-subgroup">2 ПГ</span>';

                            return `
                                <div class="kanban-card ${{status.isLive ? 'is-live' : ''}}">
                                    ${{status.isLive ? '<div class="live-badge-bar">🔥 ЗАРАЗ ЙДЕ ПАРА</div>' : ''}}
                                    ${{status.isLive ? `<div class="timer-box">${{status.timeLeftText}}</div>` : ''}}

                                    <div class="card-top">
                                        <div class="card-type-group">
                                            ${{lessonNum ? `<span class="lesson-num-badge">${{lessonNum}}</span>` : ''}}
                                            <span class="card-type">${{l.type}}</span>
                                        </div>
                                        ${{subGroupBadge}}
                                    </div>
                                    <div class="card-title">${{l.subject.replace('(П1)', '').replace('(П2)', '')}}</div>
                                    <div class="card-teacher">${{l.teacher}}</div>
                                    <div class="card-time">⏱ ${{l.time}}</div>
                                    ${{l.link ? `<div class="card-actions"><a href="${{l.link}}" target="_blank" class="${{btnClass}}">${{btnText}}</a></div>` : ''}}
                                </div>
                            `;
                        }}).join('');

                        gridHtml += `
                            <div class="kanban-column">
                                <div class="column-header">
                                    <div style="display:flex; align-items:center; gap:8px;">
                                        <span class="day-dot ${{dayDotClasses[day] || ''}}"></span>
                                        ${{daysMapUa[day] || day}}
                                    </div>
                                    ${{isToday ? '<span class="today-badge">сьогодні</span>' : ''}}
                                </div>
                                ${{cardsHtml || '<div style="font-size:0.8rem; color:var(--text-muted); text-align:center; padding:10px;">Пар немає</div>'}}
                            </div>
                        `;
                    }}

                    gridHtml += '</div>';
                    container.innerHTML = gridHtml;
                    return;
                }}

                const targetDay = (selectedDay === 'today') ? scheduleData.today : selectedDay;
                const lessons = scheduleData.schedule[targetDay] || [];
                const isToday = (targetDay === scheduleData.today);
                const filtered = filterLessons(lessons);

                let listHtml = `<div class="single-day-wrapper"><div class="kanban-column">
                    <div class="column-header">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span class="day-dot ${{dayDotClasses[targetDay] || ''}}"></span>
                            ${{daysFullUa[targetDay] || targetDay}}
                        </div>
                        ${{isToday ? '<span class="today-badge">сьогодні</span>' : ''}}
                    </div>
                `;

                if (filtered.length === 0) {{
                    listHtml += `<div style="text-align:center; padding:20px; color:var(--text-muted);">🎉 Пар немає!</div>`;
                }} else {{
                    listHtml += filtered.map(l => {{
                        const status = getLessonStatus(l.time, isToday);
                        const lessonNum = getLessonNumber(l.time);
                        const isZoom = l.link && l.link.includes('zoom');
                        const btnClass = isZoom ? 'btn-zoom' : 'btn-meet';
                        const btnText = isZoom ? '🎥 Zoom' : '🟢 Meet';

                        return `
                            <div class="kanban-card ${{status.isLive ? 'is-live' : ''}}" style="padding:16px;">
                                ${{status.isLive ? '<div class="live-badge-bar">🔥 ЗАРАЗ ЙДЕ ПАРА</div>' : ''}}
                                ${{status.isLive ? `<div class="timer-box" style="font-size:0.9rem; padding:8px;">${{status.timeLeftText}}</div>` : ''}}

                                <div class="card-top">
                                    <div class="card-type-group">
                                        ${{lessonNum ? `<span class="lesson-num-badge">${{lessonNum}}</span>` : ''}}
                                        <span class="card-type">${{l.type}}</span>
                                    </div>
                                    <span class="card-time">⏱ ${{l.time}}</span>
                                </div>
                                <div class="card-title" style="font-size:1.1rem; margin:4px 0;">${{l.subject}}</div>
                                <div class="card-teacher">👨‍🏫 ${{l.teacher}} | 📍 ${{l.room}}</div>
                                ${{l.link ? `<div class="card-actions" style="margin-top:10px;"><a href="${{l.link}}" target="_blank" class="${{btnClass}}">${{btnText}}</a></div>` : ''}}
                            </div>
                        `;
                    }}).join('');
                }}

                listHtml += '</div></div>';
                container.innerHTML = listHtml;
            }}

            async function fetchSchedule() {{
                const res = await fetch('/api/schedule');
                scheduleData = await res.json();
                renderDaysButtons();
                renderSchedule();
            }}

            fetchSchedule();
            setInterval(renderSchedule, 1000);
            setInterval(fetchSchedule, 60000);
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)