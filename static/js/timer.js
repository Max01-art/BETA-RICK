// Timer.js - Pomodoro Timer
class PomodoroTimer {
    constructor() {
        this.WORK_TIME = 25 * 60;
        this.BREAK_TIME = 5 * 60;
        this.timeLeft = this.WORK_TIME;
        this.isRunning = false;
        this.isBreak = false;
        this.interval = null;
        this.sessions = [];
        this.init();
    }
    
    init() {
        this.loadSettings();
        this.loadSessions();
        this.setupButtons();
        this.updateDisplay();
    }
    
    loadSettings() {
        const work = localStorage.getItem('timer_work') || 25;
        const breakTime = localStorage.getItem('timer_break') || 5;
        this.WORK_TIME = work * 60;
        this.BREAK_TIME = breakTime * 60;
        this.timeLeft = this.WORK_TIME;
    }
    
    setupButtons() {
        document.getElementById('startBtn')?.addEventListener('click', () => this.start());
        document.getElementById('pauseBtn')?.addEventListener('click', () => this.pause());
        document.getElementById('resetBtn')?.addEventListener('click', () => this.reset());
        
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchMode(e.target.dataset.mode));
        });
        
        document.getElementById('workDuration')?.addEventListener('change', (e) => {
            this.WORK_TIME = e.target.value * 60;
            if (!this.isBreak) this.timeLeft = this.WORK_TIME;
            this.updateDisplay();
        });
        
        document.getElementById('breakDuration')?.addEventListener('change', (e) => {
            this.BREAK_TIME = e.target.value * 60;
            if (this.isBreak) this.timeLeft = this.BREAK_TIME;
            this.updateDisplay();
        });
    }
    
    start() {
        this.isRunning = true;
        document.getElementById('startBtn').style.display = 'none';
        document.getElementById('pauseBtn').style.display = 'flex';
        this.interval = setInterval(() => this.tick(), 1000);
    }
    
    pause() {
        this.isRunning = false;
        clearInterval(this.interval);
        document.getElementById('startBtn').style.display = 'flex';
        document.getElementById('pauseBtn').style.display = 'none';
    }
    
    reset() {
        this.pause();
        this.timeLeft = this.isBreak ? this.BREAK_TIME : this.WORK_TIME;
        this.updateDisplay();
    }
    
    tick() {
        if (this.timeLeft > 0) {
            this.timeLeft--;
            this.updateDisplay();
        } else {
            this.complete();
        }
    }
    
    complete() {
        this.pause();
        if (!this.isBreak) {
            this.saveSession();
            this.isBreak = true;
            this.timeLeft = this.BREAK_TIME;
        } else {
            this.isBreak = false;
            this.timeLeft = this.WORK_TIME;
        }
        this.updateDisplay();
        this.playSound();
    }
    
    switchMode(mode) {
        this.pause();
        this.isBreak = mode === 'break';
        this.timeLeft = this.isBreak ? this.BREAK_TIME : this.WORK_TIME;
        document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
        this.updateDisplay();
    }
    
    updateDisplay() {
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        document.getElementById('timerDisplay').textContent = display;
        
        const progress = ((this.isBreak ? this.BREAK_TIME : this.WORK_TIME) - this.timeLeft) / (this.isBreak ? this.BREAK_TIME : this.WORK_TIME);
        const circle = document.getElementById('timerProgress');
        if (circle) {
            const circumference = 2 * Math.PI * 135;
            circle.style.strokeDashoffset = circumference * (1 - progress);
        }
    }
    
    saveSession() {
        const session = {
            duration: this.WORK_TIME,
            timestamp: Date.now(),
            date: new Date().toLocaleDateString()
        };
        this.sessions.push(session);
        localStorage.setItem('timer_sessions', JSON.stringify(this.sessions));
        this.updateStats();
    }
    
    loadSessions() {
        const saved = localStorage.getItem('timer_sessions');
        this.sessions = saved ? JSON.parse(saved) : [];
        this.updateStats();
    }
    
    updateStats() {
        const today = new Date().toLocaleDateString();
        const todaySessions = this.sessions.filter(s => s.date === today);
        const todayMinutes = todaySessions.reduce((sum, s) => sum + s.duration / 60, 0);
        
        document.getElementById('todayMinutes').textContent = Math.floor(todayMinutes);
        document.getElementById('todaySessions').textContent = todaySessions.length;
    }
    
    playSound() {
        const audio = new AudioContext();
        const osc = audio.createOscillator();
        const gain = audio.createGain();
        osc.connect(gain);
        gain.connect(audio.destination);
        osc.frequency.value = 800;
        gain.gain.setValueAtTime(0.3, audio.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audio.currentTime + 0.5);
        osc.start();
        osc.stop(audio.currentTime + 0.5);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('timerDisplay')) {
        window.timer = new PomodoroTimer();
    }
});
