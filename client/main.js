const clock = document.getElementById("clock");

// Update the clock every second
const updateClock = () => {
	const now = new Date();
	clock.textContent = now.toLocaleTimeString([], {
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit",
		hour12: false
	});
};

if (clock) {
	updateClock();
	setInterval(updateClock, 1000);
}

let api = 'http://127.0.0.1:8000/';
let endpoint;
let eventId;
let progressSource;

// Map stat types to icon symbols and color classes
const statTypeIcons = {
	CM: { icon: 'pointer', color: 'icon-default' },
	EA: { icon: 'star', color: 'icon-red' },
	EH: { icon: 'explosion', color: 'icon-red' },
	EQ: { icon: 'leaderboard', color: 'icon-orange' },
	ES: { icon: 'leaderboard', color: 'icon-purple' },
	TC: { icon: 'trophy', color: 'icon-yellow' },
	SI: { icon: 'trend', color: 'icon-green' },
	SM: { icon: 'route', color: 'icon-blue' },
	SS: { icon: 'strength', color: 'icon-green' },
	ST: { icon: 'donut', color: 'icon-blue' },
	WR: { icon: 'percent', color: 'icon-red' },
	WS: { icon: 'flame', color: 'icon-red' }
};

function updateStatIcon(teamData, statElementId) {
	if (!teamData || !teamData.stats || teamData.stats.length === 0) return;
	
	const statType = teamData.stats[0].type;
	const iconConfig = statTypeIcons[statType];
	
	if (iconConfig) {
		const iconEl = document.querySelector(`#${statElementId} .item-icon`);
		if (iconEl) {
			iconEl.className = `item-icon ${iconConfig.color}`;
			iconEl.innerHTML = `<svg><use href="#${iconConfig.icon}"/></svg>`;
		}
	}
}

// Toggle theme
function theme() {
    document.body.classList.toggle('dark');
}

// Hide cards for teams not playing
function hideItems(mode) {
	if (mode == 'v5') {
		document.getElementById('team2').classList.remove('hidden');
		document.getElementById('team4').classList.remove('hidden');
		document.getElementById('stat2').classList.remove('hidden');
		document.getElementById('stat4').classList.remove('hidden');
	} else {
		document.getElementById('team2').classList.add('hidden');
		document.getElementById('team4').classList.add('hidden');
		document.getElementById('stat2').classList.add('hidden');
		document.getElementById('stat4').classList.add('hidden');
	}
}

// Get event ID from SKU
async function getEvent() {
    endpoint = api + 'utilities/events/' + String(document.getElementById('sku').value);
    await fetch(endpoint).then(response => response.json()).then(data => {eventId = data.id;});
}

// Load match statistics
function getStats() {
	const progressEl = document.getElementById('progress');
	const progressFill = document.getElementById('progress-fill');
	const progressStatus = document.getElementById('progress-status');

	const showProgress = (percent, status) => {
		progressEl.classList.remove('hidden');
		progressFill.style.width = `${percent}%`;
		progressStatus.textContent = status;
	};

	const hideProgress = () => {
		progressEl.classList.add('hidden');
		progressFill.style.width = '0%';
		progressStatus.textContent = '';
	};

	if (progressSource) {
		progressSource.close();
	}

	endpoint = api + 'stats/match/' + eventId + '/' + String(document.getElementById('division').value) + '/' + String(document.getElementById('round').value) + '/' + String(document.getElementById('instance').value) + '/' + String(document.getElementById('number').value) + '/' + String(document.getElementById('recency').value);
	showProgress(0, 'Starting...');

	progressSource = new EventSource(endpoint);
	progressSource.addEventListener('progress', event => {
		const data = JSON.parse(event.data);
		const percent = data.percent ?? 0;
		const step = data.step ? data.step.replaceAll('_', ' ') : 'Working...';
		showProgress(percent, `${step} (${percent}%)`);
	});
	progressSource.addEventListener('result', event => {
		const data = JSON.parse(event.data);
		progressSource.close();
		hideProgress();
		if (Object.keys(data).length == 4) {
			hideItems('v5');
		} else {
			hideItems('iq');
		}

		const renderTeam = (teamData, teamBoxId, statBoxId) => {
			if (!teamData) return false;
			
			const teamEl = document.getElementById(teamBoxId);
			const statEl = document.getElementById(statBoxId);
			
			document.getElementById(teamBoxId + '-content').innerHTML = '<b>' + teamData.info.number + '</b> • ' + teamData.info.name + '<br>' + teamData.info.organization + '<br>' + teamData.info.city;
			
			if (teamData.stats && teamData.stats.length > 0) {
				document.getElementById(statBoxId + '-content').innerHTML = teamData.stats[0].phrase.replaceAll('%team%', '<b>' + teamData.info.number + '</b>') + ' (' + teamData.stats[0].value + ')';
				statEl.classList.remove('hidden');
				return true;
			} else {
				statEl.classList.add('hidden');
				return false;
			}
		};

		const hasStats1 = renderTeam(data.red1, 'team1', 'stat1');
		const hasStats2 = renderTeam(data.red2, 'team2', 'stat2');
		const hasStats3 = renderTeam(data.blue1, 'team3', 'stat3');
		const hasStats4 = renderTeam(data.blue2, 'team4', 'stat4');
		
		const hasAnyStats = hasStats1 || hasStats2 || hasStats3 || hasStats4;
		
		if (!hasAnyStats) {
			document.getElementById('stat1').classList.remove('hidden');
			const iconEl = document.querySelector('#stat1 .item-icon');
			if (iconEl) {
				iconEl.className = 'item-icon icon-default';
				iconEl.innerHTML = '<svg><use href="#pointer"/></svg>';
			}
			document.getElementById('stat1-content').innerHTML = 'No stats to show';
		} else {
			updateStatIcon(data.red1, 'stat1');
			updateStatIcon(data.red2, 'stat2');
			updateStatIcon(data.blue1, 'stat3');
			updateStatIcon(data.blue2, 'stat4');
		}
	});
	progressSource.addEventListener('error', event => {
		const data = event.data ? JSON.parse(event.data) : null;
		progressSource.close();
		hideProgress();
		if (data && data.message) {
			alert(data.message);
		} else {
			alert('Match not found. Make sure the match exists and that the division, round, instance, and match number are correct. If you are still seeing this error, please contact the MCDb administrator for your event.');
		}
	});
}

function nextMatch() {
	document.getElementById('number').value = parseInt(document.getElementById('number').value) + 1;
	getStats();
}

// Listeners
document.getElementById('theme').addEventListener('click', theme);
document.getElementById('refresh').addEventListener('click', getEvent);
document.getElementById('load').addEventListener('click', getStats);
document.getElementById('next').addEventListener('click', nextMatch);