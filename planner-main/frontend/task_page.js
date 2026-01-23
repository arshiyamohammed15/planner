/**
 * Task Page JavaScript
 * 
 * Handles displaying task details, comments, and @mentions.
 * Highlights @mentions within comments for better visibility.
 */

// Configuration
const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8080';
const CURRENT_USER = window.CURRENT_USER || 'mk'; // Set this from your auth system
const JWT_TOKEN = window.JWT_TOKEN || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtayIsImlhdCI6MTc2OTA4NzM4MywiZXhwIjoxNzY5MDkwOTgzfQ.HaWJu1CSmFxCE9dGSgqslCf0I-K-piC-HgL93oFmLGA';

/**
 * Fetch task details including comments from the API
 */
async function fetchTaskDetails(taskId) {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${JWT_TOKEN}`,
            },
        });

        if (!response.ok) {
            if (response.status === 401) {
                throw new Error(`Failed to fetch task: Unauthorized`);
            }
            if (response.status === 404) {
                throw new Error(`Task ${taskId} not found`);
            }
            throw new Error(`Failed to fetch task: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching task details:', error);
        throw error;
    }
}

/**
 * Fetch comments for a task
 */
async function fetchTaskComments(taskId) {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/comments`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${JWT_TOKEN}`,
            },
        });

        if (!response.ok) {
            if (response.status === 401) {
                throw new Error(`Failed to fetch comments: Unauthorized`);
            }
            throw new Error(`Failed to fetch comments: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching comments:', error);
        throw error;
    }
}

/**
 * Extract @mentions from text
 */
function extractMentions(text) {
    if (!text) return [];
    const mentionPattern = /@([a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?)/g;
    const mentions = [];
    let match;
    while ((match = mentionPattern.exec(text)) !== null) {
        mentions.push(match[1]);
    }
    return [...new Set(mentions)]; // Return unique mentions
}

/**
 * Highlight @mentions in comment text
 */
function highlightMentions(text, currentUser = null) {
    if (!text) return '';
    
    // Escape HTML to prevent XSS
    const escaped = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    
    // Highlight @mentions
    const mentionPattern = /@([a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?)/g;
    
    return escaped.replace(mentionPattern, (match, username) => {
        const isCurrentUser = currentUser && username.toLowerCase() === currentUser.toLowerCase();
        const highlightClass = isCurrentUser ? 'mention-current-user' : 'mention';
        return `<span class="${highlightClass}" data-username="${username}">@${username}</span>`;
    });
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Render a single comment
 */
function renderComment(comment, currentUser = null) {
    const mentions = extractMentions(comment.comment_text);
    const hasMentions = mentions.length > 0;
    const isMentioned = currentUser && mentions.some(m => m.toLowerCase() === currentUser.toLowerCase());
    
    const commentElement = document.createElement('div');
    commentElement.className = `comment ${isMentioned ? 'comment-mentioned' : ''}`;
    commentElement.setAttribute('data-comment-id', comment.id);
    
    const highlightedText = highlightMentions(comment.comment_text, currentUser);
    
    commentElement.innerHTML = `
        <div class="comment-header">
            <span class="comment-author">${escapeHtml(comment.user)}</span>
            <span class="comment-timestamp">${formatTimestamp(comment.timestamp)}</span>
            ${hasMentions ? '<span class="mention-badge">@mention</span>' : ''}
        </div>
        <div class="comment-body">${highlightedText}</div>
        ${mentions.length > 0 ? `
            <div class="comment-mentions">
                <span class="mentions-label">Mentioned:</span>
                ${mentions.map(m => `<span class="mention-tag">@${m}</span>`).join('')}
            </div>
        ` : ''}
    `;
    
    return commentElement;
}

/**
 * Render all comments for a task
 */
function renderComments(comments, containerId, currentUser = null) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with id "${containerId}" not found`);
        return;
    }
    
    // Clear existing comments
    container.innerHTML = '';
    
    if (comments.length === 0) {
        container.innerHTML = '<div class="no-comments">No comments yet. Be the first to comment!</div>';
        return;
    }
    
    // Render each comment
    comments.forEach(comment => {
        const commentElement = renderComment(comment, currentUser);
        container.appendChild(commentElement);
    });
}

/**
 * Render task details
 */
function renderTaskDetails(task, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with id "${containerId}" not found`);
        return;
    }
    
    const statusClass = `status-${task.status.toLowerCase().replace('_', '-')}`;
    const testTypeClass = `test-type-${task.test_type.toLowerCase()}`;
    
    container.innerHTML = `
        <div class="task-header">
            <h2 class="task-title">Task: ${escapeHtml(task.id)}</h2>
            <div class="task-meta">
                <span class="task-status ${statusClass}">${escapeHtml(task.status)}</span>
                <span class="task-type ${testTypeClass}">${escapeHtml(task.test_type)}</span>
                ${task.owner ? `<span class="task-owner">Owner: ${escapeHtml(task.owner)}</span>` : ''}
            </div>
        </div>
        <div class="task-description">
            <h3>Description</h3>
            <p>${highlightMentions(task.description, CURRENT_USER)}</p>
        </div>
        ${task.dependencies && task.dependencies.length > 0 ? `
            <div class="task-dependencies">
                <h3>Dependencies</h3>
                <ul>
                    ${task.dependencies.map(dep => `<li><a href="#task-${dep}" class="dependency-link">${escapeHtml(dep)}</a></li>`).join('')}
                </ul>
            </div>
        ` : ''}
        <div class="task-coverage">
            <span class="coverage-status">Coverage: ${escapeHtml(task.coverage_status)}</span>
        </div>
    `;
}

/**
 * Display task page with comments and mentions
 */
async function displayTaskPage(taskId, taskContainerId, commentsContainerId, currentUser = null) {
    try {
        // Show loading state
        const taskContainer = document.getElementById(taskContainerId);
        const commentsContainer = document.getElementById(commentsContainerId);
        
        if (taskContainer) {
            taskContainer.innerHTML = '<div class="loading">Loading task details...</div>';
        }
        if (commentsContainer) {
            commentsContainer.innerHTML = '<div class="loading">Loading comments...</div>';
        }
        
        // Fetch task details
        const task = await fetchTaskDetails(taskId);
        
        // Render task details
        renderTaskDetails(task, taskContainerId);
        
        // Render comments
        renderComments(task.comments, commentsContainerId, currentUser);
        
        // Highlight mentions in task description if any
        const mentions = extractMentions(task.description);
        if (mentions.length > 0 && currentUser) {
            const isMentioned = mentions.some(m => m.toLowerCase() === currentUser.toLowerCase());
            if (isMentioned) {
                const taskDesc = document.querySelector('.task-description');
                if (taskDesc) {
                    taskDesc.classList.add('task-mentioned');
                }
            }
        }
        
    } catch (error) {
        console.error('Error displaying task page:', error);
        const errorMsg = error.message || 'Failed to load task details';
        
        const taskContainer = document.getElementById(taskContainerId);
        const commentsContainer = document.getElementById(commentsContainerId);
        
        if (taskContainer) {
            taskContainer.innerHTML = `<div class="error">Error: ${escapeHtml(errorMsg)}</div>`;
        }
        if (commentsContainer) {
            commentsContainer.innerHTML = `<div class="error">Error: ${escapeHtml(errorMsg)}</div>`;
        }
    }
}

/**
 * Utility function to escape HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Initialize task page when DOM is ready
 */
function initTaskPage() {
    // Get task ID from URL or data attribute
    const taskId = getTaskIdFromUrl() || document.body.getAttribute('data-task-id');
    
    if (!taskId) {
        console.error('Task ID not found. Please provide task ID in URL or data-task-id attribute.');
        return;
    }
    
    // Display task page
    displayTaskPage(
        taskId,
        'task-details-container',
        'comments-container',
        CURRENT_USER
    );
    
    // Set up auto-refresh for comments (optional)
    if (window.AUTO_REFRESH_COMMENTS) {
        setInterval(async () => {
            try {
                const comments = await fetchTaskComments(taskId);
                renderComments(comments, 'comments-container', CURRENT_USER);
            } catch (error) {
                console.error('Error refreshing comments:', error);
            }
        }, 30000); // Refresh every 30 seconds
    }
}

/**
 * Extract task ID from URL
 */
function getTaskIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('task_id') || urlParams.get('id');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTaskPage);
} else {
    initTaskPage();
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        fetchTaskDetails,
        fetchTaskComments,
        displayTaskPage,
        renderComments,
        highlightMentions,
        extractMentions,
    };
}

