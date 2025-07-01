document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const API_BASE_URL = 'http://localhost:8000/api/v1';
    const NOTION_DASHBOARD_URL = 'https://www.notion.so/thehigherselfnetwork/agent-tasks';

    // DOM Elements
    const agentSelect = document.getElementById('agentSelect');
    const taskTypeSelect = document.getElementById('taskType');
    const dynamicFormFields = document.getElementById('dynamicFormFields');
    const taskForm = document.getElementById('taskForm');
    const resultCard = document.getElementById('resultCard');
    const taskResult = document.getElementById('taskResult');
    const recentTasksList = document.getElementById('recentTasksList');
    const notionLink = document.getElementById('notionLink');
    const stars = document.querySelectorAll('.star');
    const submitFeedbackBtn = document.getElementById('submitFeedback');

    // Set Notion Dashboard URL
    notionLink.href = NOTION_DASHBOARD_URL;

    // Task type definitions by agent
    const taskTypes = {
        content_creator: [
            { value: 'blog_post', label: 'Blog Post' },
            { value: 'social_media', label: 'Social Media Post' },
            { value: 'email_newsletter', label: 'Email Newsletter' },
            { value: 'course_content', label: 'Course Content' }
        ],
        marketing_assistant: [
            { value: 'campaign_plan', label: 'Marketing Campaign Plan' },
            { value: 'ad_copy', label: 'Advertisement Copy' },
            { value: 'audience_analysis', label: 'Audience Analysis' },
            { value: 'content_calendar', label: 'Content Calendar' }
        ],
        research_analyst: [
            { value: 'market_research', label: 'Market Research' },
            { value: 'competitor_analysis', label: 'Competitor Analysis' },
            { value: 'trend_report', label: 'Trend Report' },
            { value: 'literature_review', label: 'Literature Review' }
        ],
        community_manager: [
            { value: 'community_update', label: 'Community Update' },
            { value: 'engagement_strategy', label: 'Engagement Strategy' },
            { value: 'member_spotlight', label: 'Member Spotlight' },
            { value: 'event_planning', label: 'Event Planning' }
        ]
    };

    // Dynamic form fields by task type
    const formFieldTemplates = {
        blog_post: `
            <div class="mb-3">
                <label for="title" class="form-label">Blog Title</label>
                <input type="text" class="form-control" id="title" required>
            </div>
            <div class="mb-3">
                <label for="keywords" class="form-label">Target Keywords</label>
                <input type="text" class="form-control" id="keywords" placeholder="Comma-separated keywords">
            </div>
            <div class="mb-3">
                <label for="wordCount" class="form-label">Word Count</label>
                <select class="form-select" id="wordCount">
                    <option value="500">Short (500 words)</option>
                    <option value="1000" selected>Medium (1000 words)</option>
                    <option value="2000">Long (2000 words)</option>
                </select>
            </div>
            <div class="mb-3">
                <label for="tone" class="form-label">Tone</label>
                <select class="form-select" id="tone">
                    <option value="informative" selected>Informative</option>
                    <option value="conversational">Conversational</option>
                    <option value="inspirational">Inspirational</option>
                    <option value="professional">Professional</option>
                </select>
            </div>
        `,
        social_media: `
            <div class="mb-3">
                <label for="platform" class="form-label">Platform</label>
                <select class="form-select" id="platform">
                    <option value="instagram" selected>Instagram</option>
                    <option value="facebook">Facebook</option>
                    <option value="twitter">Twitter</option>
                    <option value="linkedin">LinkedIn</option>
                </select>
            </div>
            <div class="mb-3">
                <label for="topic" class="form-label">Topic</label>
                <input type="text" class="form-control" id="topic" required>
            </div>
            <div class="mb-3">
                <label for="includeHashtags" class="form-check-label">
                    <input type="checkbox" class="form-check-input" id="includeHashtags" checked>
                    Include Hashtags
                </label>
            </div>
            <div class="mb-3">
                <label for="callToAction" class="form-label">Call to Action</label>
                <input type="text" class="form-control" id="callToAction">
            </div>
        `,
        // Add more templates for other task types as needed
    };

    // Populate task types based on selected agent
    agentSelect.addEventListener('change', function() {
        const selectedAgent = this.value;
        taskTypeSelect.innerHTML = '<option value="" selected disabled>Select task type...</option>';

        if (taskTypes[selectedAgent]) {
            taskTypes[selectedAgent].forEach(type => {
                const option = document.createElement('option');
                option.value = type.value;
                option.textContent = type.label;
                taskTypeSelect.appendChild(option);
            });
        }

        // Clear dynamic form fields
        dynamicFormFields.innerHTML = '';
    });

    // Populate dynamic form fields based on selected task type
    taskTypeSelect.addEventListener('change', function() {
        const selectedTaskType = this.value;

        if (formFieldTemplates[selectedTaskType]) {
            dynamicFormFields.innerHTML = formFieldTemplates[selectedTaskType];
        } else {
            // Default form fields if no specific template exists
            dynamicFormFields.innerHTML = `
                <div class="mb-3">
                    <label for="taskTitle" class="form-label">Task Title</label>
                    <input type="text" class="form-control" id="taskTitle" required>
                </div>
                <div class="mb-3">
                    <label for="taskDetails" class="form-label">Task Details</label>
                    <textarea class="form-control" id="taskDetails" rows="3" required></textarea>
                </div>
            `;
        }
    });

    // Handle form submission
    taskForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Collect form data
        const formData = {
            agent_id: agentSelect.value,
            task_type: taskTypeSelect.value,
            priority: document.getElementById('priority').value,
            due_date: document.getElementById('dueDate').value || null,
            description: document.getElementById('taskDescription').value,
            parameters: {}
        };

        // Collect dynamic form fields
        dynamicFormFields.querySelectorAll('input, select, textarea').forEach(field => {
            if (field.type === 'checkbox') {
                formData.parameters[field.id] = field.checked;
            } else {
                formData.parameters[field.id] = field.value;
            }
        });

        // Show loading state
        const submitBtn = taskForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = 'Processing...';
        submitBtn.disabled = true;

        // Submit to API
        submitTaskToAPI(formData)
            .then(response => {
                // Display result
                showTaskResult(response);

                // Add to recent tasks
                addToRecentTasks(response);

                // Reset form
                taskForm.reset();
                dynamicFormFields.innerHTML = '';

                // Create Notion task
                createNotionTask(formData, response.task_id);
            })
            .catch(error => {
                console.error('Error submitting task:', error);
                alert('There was an error submitting your task. Please try again.');
            })
            .finally(() => {
                // Reset button state
                submitBtn.textContent = originalBtnText;
                submitBtn.disabled = false;
            });
    });

    // Handle star rating
    stars.forEach(star => {
        star.addEventListener('click', function() {
            const rating = this.getAttribute('data-rating');

            // Reset all stars
            stars.forEach(s => s.classList.remove('selected'));

            // Select clicked star and all stars before it
            stars.forEach(s => {
                if (s.getAttribute('data-rating') <= rating) {
                    s.classList.add('selected');
                }
            });

            // Store rating
            submitFeedbackBtn.setAttribute('data-rating', rating);
        });
    });

    // Handle feedback submission
    submitFeedbackBtn.addEventListener('click', function() {
        const rating = this.getAttribute('data-rating');
        const feedback = document.getElementById('feedbackText').value;
        const taskId = resultCard.getAttribute('data-task-id');

        if (!rating) {
            alert('Please select a rating before submitting feedback.');
            return;
        }

        // Submit feedback to API
        submitFeedbackToAPI(taskId, rating, feedback)
            .then(() => {
                alert('Thank you for your feedback!');
                document.getElementById('feedbackText').value = '';
                stars.forEach(s => s.classList.remove('selected'));
                submitFeedbackBtn.removeAttribute('data-rating');
            })
            .catch(error => {
                console.error('Error submitting feedback:', error);
                alert('There was an error submitting your feedback. Please try again.');
            });
    });

    // Load recent tasks on page load
    loadRecentTasks();

    // API Functions
    async function submitTaskToAPI(formData) {
        // In a real implementation, this would call your actual API
        console.log('Submitting task to API:', formData);

        // Simulate API call for demo purposes
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    task_id: 'task_' + Date.now(),
                    status: 'completed',
                    result: generateMockResult(formData),
                    created_at: new Date().toISOString()
                });
            }, 2000);
        });
    }

    async function submitFeedbackToAPI(taskId, rating, feedback) {
        // In a real implementation, this would call your actual API
        console.log('Submitting feedback:', { taskId, rating, feedback });

        // Simulate API call for demo purposes
        return new Promise(resolve => {
            setTimeout(resolve, 1000);
        });
    }

    async function loadRecentTasks() {
        // In a real implementation, this would call your actual API
        console.log('Loading recent tasks');

        // Simulate API call for demo purposes
        const mockTasks = [
            {
                task_id: 'task_1',
                agent_id: 'content_creator',
                task_type: 'blog_post',
                status: 'completed',
                created_at: '2025-05-13T15:30:00Z',
                title: 'Meditation Benefits for Beginners'
            },
            {
                task_id: 'task_2',
                agent_id: 'marketing_assistant',
                task_type: 'campaign_plan',
                status: 'pending',
                created_at: '2025-05-14T09:15:00Z',
                title: 'Summer Course Launch Campaign'
            }
        ];

        displayRecentTasks(mockTasks);
    }

    async function createNotionTask(formData, taskId) {
        // In a real implementation, this would call your API to create a Notion task
        console.log('Creating Notion task:', { formData, taskId });

        // Simulate API call for demo purposes
        return new Promise(resolve => {
            setTimeout(resolve, 1000);
        });
    }

    // Helper Functions
    function showTaskResult(response) {
        taskResult.innerHTML = response.result;
        resultCard.style.display = 'block';
        resultCard.setAttribute('data-task-id', response.task_id);
        resultCard.scrollIntoView({ behavior: 'smooth' });
    }

    function addToRecentTasks(task) {
        const taskItem = document.createElement('li');
        taskItem.className = 'list-group-item task-item';
        taskItem.innerHTML = `
            <div class="d-flex justify-content-between">
                <div>
                    <strong>${task.task_type.replace('_', ' ')}</strong>
                    <div class="task-date">${formatDate(task.created_at)}</div>
                </div>
                <span class="task-status-completed">Completed</span>
            </div>
        `;

        // Add to the beginning of the list
        if (recentTasksList.firstChild) {
            recentTasksList.insertBefore(taskItem, recentTasksList.firstChild);
        } else {
            recentTasksList.appendChild(taskItem);
        }
    }

    function displayRecentTasks(tasks) {
        recentTasksList.innerHTML = '';

        tasks.forEach(task => {
            const taskItem = document.createElement('li');
            taskItem.className = 'list-group-item task-item';

            let statusClass = 'task-status-pending';
            if (task.status === 'completed') statusClass = 'task-status-completed';
            if (task.status === 'failed') statusClass = 'task-status-failed';

            taskItem.innerHTML = `
                <div class="d-flex justify-content-between">
                    <div>
                        <strong>${task.task_type.replace('_', ' ')}</strong>
                        <div class="task-date">${formatDate(task.created_at)}</div>
                    </div>
                    <span class="${statusClass}">${task.status}</span>
                </div>
            `;

            recentTasksList.appendChild(taskItem);
        });
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function generateMockResult(formData) {
        // Generate mock results based on task type
        if (formData.task_type === 'blog_post') {
            return `<h3>Blog Post: ${formData.parameters.title || 'Untitled'}</h3>
                <p>This is a sample blog post about ${formData.parameters.title || 'the requested topic'}.
                In a real implementation, this would be generated by your AI agent.</p>
                <p>The post would be approximately ${formData.parameters.wordCount || 1000} words and written in a
                ${formData.parameters.tone || 'informative'} tone.</p>
                <p>Keywords: ${formData.parameters.keywords || 'No keywords specified'}</p>`;
        }

        if (formData.task_type === 'social_media') {
            return `<h3>Social Media Post for ${formData.parameters.platform || 'Instagram'}</h3>
                <p><strong>Post:</strong> Check out our latest insights on ${formData.parameters.topic || 'this topic'}!
                ${formData.parameters.callToAction || 'Learn more at our website.'}</p>
                ${formData.parameters.includeHashtags ? '<p><strong>Hashtags:</strong> #HigherSelfNetwork #PersonalGrowth #Mindfulness</p>' : ''}`;
        }

        // Default response for other task types
        return `<h3>Task Completed</h3>
            <p>Your ${formData.task_type.replace('_', ' ')} task has been processed.</p>
            <p>In a real implementation, this would contain the actual output from your AI agent.</p>`;
    }
});
