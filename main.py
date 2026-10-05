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
        5: "saturday",
        6: "sunday",
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
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-gradient: #09090b;
                --card-bg: #121215;
                --card-border: rgba(255, 255, 255, 0.08);
                --accent-purple: #a855f7;
                --accent-cyan: #06b6d4;
                --accent-pink: #ec4899;
                --text-main: #f4f4f5;
                --text-muted: #a1a1aa;
                --live-glow: rgba(236, 72, 153, 0.3);
            }}

            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}

            body {{
                font-family: 'Plus Jakarta Sans', sans-serif;
                background-color: var(--bg-gradient);
                color: var(--text-main);
                padding: 20px 15px 60px;
                min-height: 100vh;
                position: relative;
                overflow-x: hidden;
            }}

            .bg-coconut {{
                position: fixed;
                font-size: 5rem;
                opacity: 0.05;
                user-select: none;
                pointer-events: none;
                z-index: 0;
                filter: blur(1px);
                animation: float 12s ease-in-out infinite alternate;
            }}
            .c1 {{ top: 8%; left: 5%; transform: rotate(-15deg); }}
            .c2 {{ top: 60%; right: 4%; transform: rotate(25deg); animation-delay: -4s; }}
            .c3 {{ bottom: 10%; left: 10%; transform: rotate(10deg); animation-delay: -7s; }}

            @keyframes float {{
                0% {{ transform: translateY(0) rotate(0deg); }}
                100% {{ transform: translateY(-25px) rotate(15deg); }}
            }}

            .container {{
                max-width: 850px;
                margin: 0 auto;
                position: relative;
                z-index: 1;
            }}

            header {{
                text-align: center;
                margin-bottom: 25px;
            }}

            h1 {{
                font-size: 2.2rem;
                font-weight: 800;
                color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
            }}

            .week-info {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: #18181b;
                border: 1px solid var(--card-border);
                padding: 8px 18px;
                border-radius: 30px;
                margin-top: 12px;
                font-size: 0.9rem;
                color: #e4e4e7;
            }}

            .week-info span {{
                color: var(--accent-cyan);
                font-weight: 700;
            }}

            /* ДНІ ТИЖНЯ ФІЛЬТР */
            .days-filter {{
                display: flex;
                justify-content: center;
                gap: 8px;
                margin: 20px 0 15px;
                flex-wrap: wrap;
            }}

            .day-btn {{
                background: #18181b;
                border: 1px solid var(--card-border);
                color: var(--text-muted);
                padding: 8px 14px;
                border-radius: 12px;
                font-family: inherit;
                font-weight: 700;
                font-size: 0.88rem;
                cursor: pointer;
                transition: all 0.25 ease;
                display: flex;
                align-items: center;
                gap: 5px;
            }}

            .day-btn:hover {{
                background: #27272a;
                color: #fff;
            }}

            .day-btn.active {{
                background: var(--accent-cyan);
                color: #000;
                border-color: transparent;
                box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);
            }}

            .day-btn.is-today-btn {{
                border-color: rgba(6, 182, 212, 0.5);
            }}

            /* ПІДГРУПИ ФІЛЬТР */
            .subgroup-filter {{
                display: flex;
                justify-content: center;
                gap: 8px;
                margin-bottom: 30px;
            }}

            .filter-btn {{
                background: #18181b;
                border: 1px solid var(--card-border);
                color: var(--text-muted);
                padding: 6px 14px;
                border-radius: 10px;
                font-family: inherit;
                font-size: 0.82rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.25s ease;
            }}

            .filter-btn:hover {{
                background: #27272a;
                color: #fff;
            }}

            .filter-btn.active {{
                background: var(--accent-purple);
                color: #fff;
                border-color: transparent;
                box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3);
            }}

            .day-card {{
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 20px;
                padding: 22px;
                margin-bottom: 25px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                transition: transform 0.2s ease, border-color 0.3s ease;
            }}

            .day-card.is-today {{
                border-color: rgba(6, 182, 212, 0.4);
                box-shadow: 0 0 25px rgba(6, 182, 212, 0.1);
            }}

            .day-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 18px;
                padding-bottom: 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }}

            .day-title {{
                font-size: 1.35rem;
                font-weight: 700;
                color: #f4f4f5;
                display: flex;
                align-items: center;
                gap: 10px;
            }}

            .today-badge {{
                background: var(--accent-cyan);
                color: #000;
                font-size: 0.75rem;
                font-weight: 800;
                padding: 3px 10px;
                border-radius: 20px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            .lesson {{
                position: relative;
                background: #18181b;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 14px;
                padding: 16px 18px;
                margin-bottom: 12px;
                transition: all 0.3s ease;
            }}

            .lesson:last-child {{
                margin-bottom: 0;
            }}

            .lesson.is-live {{
                background: #201322;
                border-color: rgba(236, 72, 153, 0.6);
                box-shadow: 0 0 20px var(--live-glow);
                animation: pulse-border 2s infinite alternate;
            }}

            @keyframes pulse-border {{
                0% {{ border-color: rgba(236, 72, 153, 0.4); }}
                100% {{ border-color: rgba(236, 72, 153, 0.8); }}
            }}

            .live-indicator {{
                position: absolute;
                top: 14px;
                right: 14px;
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 0.75rem;
                font-weight: 700;
                color: #f472b6;
            }}

            .live-dot {{
                width: 8px;
                height: 8px;
                background: #f472b6;
                border-radius: 50%;
                box-shadow: 0 0 8px #f472b6;
                animation: blink 1.2s infinite;
            }}

            @keyframes blink {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.3; }}
            }}

            .lesson-time {{
                font-weight: 700;
                color: #38bdf8;
                font-size: 0.95rem;
                margin-bottom: 6px;
            }}

            .lesson-subject {{
                font-size: 1.1rem;
                font-weight: 700;
                color: #ffffff;
                margin-bottom: 6px;
            }}

            .lesson-type {{
                display: inline-block;
                font-size: 0.75rem;
                font-weight: 600;
                padding: 2px 8px;
                border-radius: 6px;
                background: rgba(168, 85, 247, 0.2);
                color: #c084fc;
                margin-left: 8px;
            }}

            .lesson-meta {{
                font-size: 0.88rem;
                color: var(--text-muted);
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin-top: 8px;
            }}

            .link-btn {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                margin-top: 12px;
                padding: 8px 16px;
                background: #27272a;
                border: 1px solid var(--accent-cyan);
                color: #38bdf8;
                text-decoration: none;
                border-radius: 10px;
                font-size: 0.85rem;
                font-weight: 700;
                transition: all 0.3s ease;
            }}

            .link-btn:hover {{
                background: var(--accent-cyan);
                color: #000;
            }}

            .no-lessons {{
                text-align: center;
                padding: 40px 20px;
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 20px;
                color: var(--text-muted);
                font-weight: 600;
            }}
        </style>
    </head>
    <body>

        <div class="bg-coconut c1">🥥</div>
        <div class="bg-coconut c2">🥥</div>
        <div class="bg-coconut c3">🥥</div>

        <div class="container">
            <header>
                <h1>🥥 Розклад Занять 🥥</h1>
                <div class="week-info">Тиждень: <span>{week_label}</span></div>
            </header>

            <div class="days-filter" id="days-filter-container">
                <!-- Кнопки днів додадуться через JS -->
            </div>

            <div class="subgroup-filter">
                <button class="filter-btn active" onclick="setSubgroupFilter('all')">Повний розклад</button>
                <button class="filter-btn" onclick="setSubgroupFilter('П1')">Підгрупа 1 (П1)</button>
                <button class="filter-btn" onclick="setSubgroupFilter('П2')">Підгрупа 2 (П2)</button>
            </div>

            <div id="schedule-container">Завантаження розкладу...</div>
        </div>

        <script>
            let currentSubgroup = 'all';
            let selectedDay = 'today'; // 'today', 'all', або конкретний день 'monday'
            let scheduleData = null;

            const daysMapUa = {{
                monday: 'Пн', tuesday: 'Вт', wednesday: 'Ср',
                thursday: 'Чт', friday: "Пт", saturday: 'Сб'
            }};

            const daysFullUa = {{
                monday: 'Понеділок', tuesday: 'Вівторок', wednesday: 'Середа',
                thursday: 'Четвер', friday: "П'ятниця", saturday: 'Субота'
            }};

            function setDayFilter(day) {{
                selectedDay = day;
                renderDaysButtons();
                renderSchedule();
            }}

            function setSubgroupFilter(filter) {{
                currentSubgroup = filter;
                document.querySelectorAll('.subgroup-filter .filter-btn').forEach(btn => {{
                    btn.classList.toggle('active', btn.getAttribute('onclick').includes(`'${{filter}}'`));
                }});
                renderSchedule();
            }}

            function renderDaysButtons() {{
                if (!scheduleData) return;

                const container = document.getElementById('days-filter-container');
                const today = scheduleData.today;

                let html = `
                    <button class="day-btn ${{selectedDay === 'today' ? 'active' : ''}} is-today-btn" onclick="setDayFilter('today')">
                        ✨ Сьогодні
                    </button>
                `;

                for (const [dayKey, dayShort] of Object.entries(daysMapUa)) {{
                    const isTodayDay = (dayKey === today);
                    const isActive = (selectedDay === dayKey);

                    html += `
                        <button class="day-btn ${{isActive ? 'active' : ''}} ${{isTodayDay ? 'is-today-btn' : ''}}" onclick="setDayFilter('${{dayKey}}')">
                            ${{dayShort}}
                        </button>
                    `;
                }}

                html += `
                    <button class="day-btn ${{selectedDay === 'all' ? 'active' : ''}}" onclick="setDayFilter('all')">
                        📅 Всі дні
                    </button>
                `;

                container.innerHTML = html;
            }}

            function isLessonLive(timeStr, isToday) {{
                if (!isToday) return false;

                try {{
                    const [startStr, endStr] = timeStr.split(' - ');
                    const [startH, startM] = startStr.split(':').map(Number);
                    const [endH, endM] = endStr.split(':').map(Number);

                    const now = new Date();
                    const currentMinutes = now.getHours() * 60 + now.getMinutes();
                    const startMinutes = startH * 60 + startM;
                    const endMinutes = endH * 60 + endM;

                    return currentMinutes >= startMinutes && currentMinutes <= endMinutes;
                }} catch (e) {{
                    return false;
                }}
            }}

            function renderSchedule() {{
                if (!scheduleData) return;

                const container = document.getElementById('schedule-container');
                container.innerHTML = '';

                let daysToDisplay = [];

                if (selectedDay === 'today') {{
                    daysToDisplay = [scheduleData.today];
                }} else if (selectedDay === 'all') {{
                    daysToDisplay = Object.keys(scheduleData.schedule);
                }} else {{
                    daysToDisplay = [selectedDay];
                }}

                let renderedCount = 0;

                for (const day of daysToDisplay) {{
                    const lessons = scheduleData.schedule[day] || [];
                    const isToday = (day === scheduleData.today);

                    const filteredLessons = lessons.filter(l => {{
                        if (currentSubgroup === 'all') return true;
                        if (l.subject.includes('(П1)') && currentSubgroup === 'П2') return false;
                        if (l.subject.includes('(П2)') && currentSubgroup === 'П1') return false;
                        return true;
                    }});

                    if (filteredLessons.length === 0 && selectedDay !== 'today' && selectedDay !== day) continue;

                    renderedCount++;

                    let lessonsHtml = '';
                    if (filteredLessons.length === 0) {{
                        lessonsHtml = `<div style="color: var(--text-muted); font-size: 0.9rem; padding: 10px 0;">🎉 Немає пар на цей день!</div>`;
                    }} else {{
                        lessonsHtml = filteredLessons.map(l => {{
                            const live = isLessonLive(l.time, isToday);

                            return `
                                <div class="lesson ${{live ? 'is-live' : ''}}">
                                    ${{live ? '<div class="live-indicator"><div class="live-dot"></div> ЗАРАЗ ЙДЕ ПАРА</div>' : ''}}
                                    <div class="lesson-time">⏱ ${{l.time}}</div>
                                    <div class="lesson-subject">
                                        ${{l.subject}}
                                        <span class="lesson-type">${{l.type}}</span>
                                    </div>
                                    <div class="lesson-meta">
                                        <span>👨‍‍🏫 ${{l.teacher}}</span>
                                        <span>📍 ${{l.room}}</span>
                                    </div>
                                    ${{l.link ? `<a class="link-btn" href="${{l.link}}" target="_blank">🔗 Приєднатися до пари</a>` : `<span style="font-size: 0.8rem; color: #52525b; display: block; margin-top: 8px;">🔗 Посилання ще не додано</span>`}}
                                </div>
                            `;
                        }}).join('');
                    }}

                    container.innerHTML += `
                        <div class="day-card ${{isToday ? 'is-today' : ''}}">
                            <div class="day-header">
                                <h2 class="day-title">
                                    ${{daysFullUa[day] || day}}
                                </h2>
                                ${{isToday ? '<span class="today-badge">Сьогодні</span>' : ''}}
                            </div>
                            ${{lessonsHtml}}
                        </div>
                    `;
                }}

                if (renderedCount === 0) {{
                    container.innerHTML = `<div class="no-lessons">🎉 Пар на обраний день немає!</div>`;
                }}
            }}

            async function fetchSchedule() {{
                const res = await fetch('/api/schedule');
                scheduleData = await res.json();
                renderDaysButtons();
                renderSchedule();
            }}

            fetchSchedule();
            setInterval(fetchSchedule, 60000);
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 50)
    print("🚀 СЕРВЕР ЗАПУЩЕНО!")
    print("🔗 Твоє посилання на сайт: http://127.0.0.1:8000")
    print("🔗 Запит посилання на поточну пару: http://127.0.0.1:8000/get-link")
    print("=" * 50 + "\n")

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)