const API_BASE = (window.location.hostname === 'localhost') ? 'http://localhost:8000/api/v1' : '/api/v1';

function setStatus(msg) {
    document.getElementById('status').innerText = msg;
}

async function apiRequest(path, method = 'GET', body = null, token = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}${path}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
    });
    return res.json();
}

let token = null;

document.getElementById('loginForm').addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const userId = Number(document.getElementById('userId').value.trim());
    const username = document.getElementById('username').value.trim();
    const firstName = document.getElementById('firstName').value.trim();
    setStatus('Logging in...');
    try {
        const resp = await apiRequest('/auth/login', 'POST', { user_id: userId, username, first_name: firstName });
        if (resp.ok && resp.token) {
            token = resp.token;
            setStatus(`Logged in as ${username} (role=${resp.role})`);
        } else {
            setStatus(`Login failed: ${resp.message || JSON.stringify(resp)}`);
        }
    } catch (err) {
        setStatus('Login error: ' + err.message);
    }
});

document.getElementById('loadMembers').addEventListener('click', async () => {
    const groupId = Number(document.getElementById('groupId').value.trim());
    if (!groupId) return setStatus('Enter group id');
    setStatus('Loading members...');
    try {
        const resp = await apiRequest(`/groups/${groupId}/members?page=1&page_size=50`, 'GET', null, token);
        if (resp.ok) {
            const el = document.getElementById('members');
            el.innerHTML = '';
            resp.members.forEach(m => {
                const node = document.createElement('div');
                node.className = 'py-1 border-b';
                node.textContent = `${m.user_id} — ${m.username || m.first_name || ''}`;
                el.appendChild(node);
            });
            setStatus(`Loaded ${resp.members.length} members`);
        } else {
            setStatus('Members fetch failed');
        }
    } catch (err) {
        setStatus('Members error: ' + err.message);
    }
});

document.getElementById('loadBlacklist').addEventListener('click', async () => {
    const groupId = Number(document.getElementById('groupId').value.trim());
    if (!groupId) return setStatus('Enter group id');
    setStatus('Loading blacklist...');
    try {
        const resp = await apiRequest(`/groups/${groupId}/blacklist?page=1&page_size=50`, 'GET', null, token);
        if (resp.ok) {
            const el = document.getElementById('blacklist');
            el.innerHTML = '';
            resp.entries.forEach(e => {
                const node = document.createElement('div');
                node.className = 'py-1 border-b';
                node.textContent = `${e.user_id} — ${e.username || ''} — ${e.reason || ''}`;
                el.appendChild(node);
            });
            setStatus(`Loaded ${resp.entries.length} blacklist entries`);
        } else {
            setStatus('Blacklist fetch failed');
        }
    } catch (err) {
        setStatus('Blacklist error: ' + err.message);
    }
});

