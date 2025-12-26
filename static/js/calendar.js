// Calendar.js
class Calendar {
    constructor() {
        this.currentDate = new Date();
        this.works = [];
        this.init();
    }
    
    async init() {
        await this.loadWorks();
        this.render();
        this.setupEvents();
    }
    
    async loadWorks() {
        try {
            const res = await fetch('/api/works');
            const data = await res.json();
            this.works = data.works || [];
        } catch (e) {
            console.error('Failed to load works:', e);
        }
    }
    
    render() {
        const grid = document.getElementById('calendar');
        if (!grid) return;
        
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        
        document.getElementById('monthYear').textContent = 
            new Date(year, month).toLocaleDateString('lv-LV', { year: 'numeric', month: 'long' });
        
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        
        let html = '<div class="calendar-days">';
        ['P', 'O', 'T', 'C', 'Pk', 'S', 'Sv'].forEach(day => {
            html += `<div class="calendar-day-header">${day}</div>`;
        });
        html += '</div><div class="calendar-dates">';
        
        for (let i = 0; i < (firstDay || 7) - 1; i++) {
            html += '<div class="calendar-date empty"></div>';
        }
        
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month, day);
            const dateStr = date.toISOString().split('T')[0];
            const dayWorks = this.works.filter(w => w.date === dateStr);
            const isToday = dateStr === new Date().toISOString().split('T')[0];
            
            html += `<div class="calendar-date ${isToday ? 'today' : ''}" data-date="${dateStr}">
                <span>${day}</span>
                ${dayWorks.length ? `<div class="work-dots">${'•'.repeat(Math.min(dayWorks.length, 3))}</div>` : ''}
            </div>`;
        }
        
        html += '</div>';
        grid.innerHTML = html;
    }
    
    setupEvents() {
        document.getElementById('prevMonth')?.addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this.render();
        });
        
        document.getElementById('nextMonth')?.addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this.render();
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('calendar')) {
        new Calendar();
    }
});
