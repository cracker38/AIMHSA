/**
 * AIMHSA Professional Dashboard JavaScript
 * Enhanced version with full professional functionality
 */

(() => {
    'use strict';

    // API Configuration
    let apiRoot;
    try {
        const loc = window.location;
        // Check if running on Hugging Face Spaces
        if (loc.hostname.includes('.hf.space')) {
            // Hugging Face Spaces - use current origin
            apiRoot = loc.origin;
        } else if (loc.port === '8000') {
            // Local development with frontend on 8000
            apiRoot = `${loc.protocol}//${loc.hostname}:7860`;
        } else if (loc.port === '7860' || loc.port === '') {
            // Local development or production without port
            apiRoot = loc.origin;
        } else {
            // Default fallback - use current origin
            apiRoot = loc.origin;
        }
    } catch (_) {
        apiRoot = window.location.origin;
    }
    const API_ROOT = apiRoot;
    
    // Helper function to create API fetch with headers
    function apiFetch(endpoint, options = {}) {
        const url = `${API_ROOT}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        // Add professional ID header if available
        if (currentProfessional?.id || currentProfessional?.professional_id) {
            const profId = currentProfessional.id || currentProfessional.professional_id;
            headers['X-Professional-ID'] = String(profId);
        }
        
        return fetch(url, {
            ...options,
            headers
        });
    }
    
    console.log('🌐 Professional Dashboard API Root:', API_ROOT);

    // Global variables
    let currentSection = 'dashboard';
    let currentProfessional = null;
    let charts = {};
    let dataTables = {};

    // Initialize when DOM is ready
    $(document).ready(function() {
        console.log('🧑‍⚕️ Professional Dashboard Initializing...');
        
        // Check if professional is logged in
        const professionalData = localStorage.getItem('aimhsa_professional');
        if (!professionalData) {
            window.location.href = '/login';
            return;
        }
        
        currentProfessional = JSON.parse(professionalData);
        console.log('👤 Current Professional:', currentProfessional);
        
        // Ensure we have the professional ID
        if (!currentProfessional.id && currentProfessional.professional_id) {
            currentProfessional.id = currentProfessional.professional_id;
        }
        
        if (!currentProfessional.id) {
            console.error('❌ No professional ID found in localStorage');
            console.error('❌ Professional data:', currentProfessional);
            window.location.href = '/login';
            return;
        }
        
        console.log('✅ Professional ID confirmed:', currentProfessional.id);
        
        // Initialize components
        initializeNavigation();
        initializeDataTables();
        initializeCharts();
        initializeEventHandlers();
        
        // Update UI with professional information
        updateProfessionalUI();
        
        // Load initial data
        loadDashboardData();
        
        // Start auto-refresh
        startAutoRefresh();
        
        console.log('✅ Professional Dashboard Initialized');
    });

    /**
     * Update professional UI elements
     */
    function updateProfessionalUI() {
        console.log('🎨 Updating professional UI...');
        
        // Update professional name in navbar and sidebar
        const professionalName = currentProfessional.name || 'Professional';
        $('#professionalName').text(professionalName);
        $('#professionalNameSidebar').text(professionalName);
        
        // Update professional role/specialization if available
        if (currentProfessional.specialization) {
            $('#professionalRole').text(currentProfessional.specialization);
        }
        
        console.log('✅ Professional UI updated');
    }

    /**
     * Initialize navigation
     */
    function initializeNavigation() {
        $('.nav-link[data-section]').on('click', function(e) {
            e.preventDefault();
            const section = $(this).data('section');
            showSection(section);
        });
    }

    /**
     * Show specific section
     */
    function showSection(section) {
        console.log('🔄 Switching to section:', section);
        
        // Hide all sections
        $('.content-section').hide();
        
        // Show selected section
        $(`#${section}-section`).show();
        
        // Update active nav link
        $('.nav-link').removeClass('active');
        $(`.nav-link[data-section="${section}"]`).addClass('active');
        
        // Update page title
        const titles = {
            'dashboard': 'Dashboard',
            'sessions': 'My Sessions',
            'patients': 'My Patients',
            'notifications': 'Notifications',
            'profile': 'My Profile',
            'reports': 'Reports',
            'settings': 'Settings'
        };
        $('#pageTitle').text(titles[section] || 'Dashboard');
        
        currentSection = section;
        
        // Load section-specific data
            loadSectionData(section);
    }

    /**
     * Load section-specific data
     */
    function loadSectionData(section) {
        console.log('📊 Loading data for section:', section);
        
        switch(section) {
            case 'dashboard':
                loadDashboardStats();
                break;
            case 'sessions':
                loadSessions();
                break;
            case 'patients':
                loadPatients();
                break;
            case 'notifications':
                loadNotifications();
                break;
            case 'profile':
                loadProfile();
                break;
            case 'reports':
                loadReports();
                break;
        }
    }
    
    /**
     * Load dashboard statistics
     */
    function loadDashboardStats() {
        console.log('📈 Loading dashboard stats...');
        
        apiFetch('/professional/dashboard-stats')
            .then(response => response.json())
            .then(data => {
                console.log('📊 Dashboard stats received:', data);
                
                // Update KPI cards
                $('#totalSessions').text(data.totalSessions || data.total_sessions || 0);
                $('#unreadNotifications').text(data.unreadNotifications || data.unread_notifications || 0);
                $('#upcomingToday').text(data.upcomingToday || data.today_sessions || 0);
                $('#highRiskSessions').text(data.highRiskCases || data.high_risk_sessions || 0);
                
                // Update notification badge
                $('#notificationCount').text(data.unreadNotifications || data.unread_notifications || 0);
            })
            .catch(error => {
                console.error('❌ Error loading dashboard stats:', error);
            });
    }
    
    /**
     * Load sessions
     */
    function loadSessions() {
        console.log('📅 Loading sessions...');
        const tbody = $('#sessionsTableBody');
        tbody.html('<tr><td colspan="7" class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>');
        
        apiFetch('/professional/sessions')
            .then(response => response.json())
            .then(data => {
                console.log('📅 Sessions data received:', data);
                tbody.empty();

                // Handle both array and object with sessions property
                const sessions = Array.isArray(data) ? data : (data.sessions || []);
                
                if (sessions && sessions.length > 0) {
                    sessions.forEach(session => {
                        const riskClass = getRiskClass(session.riskLevel || session.risk_level);
                        const statusClass = getStatusClass(session.bookingStatus || session.booking_status);
                        const createdTs = session.createdTs || session.created_ts;
                        const createdDate = createdTs ? new Date(createdTs * 1000).toLocaleDateString() : 'N/A';
                        const scheduledDate = session.scheduledDatetime || session.scheduled_datetime;
                        const scheduledDateStr = scheduledDate ? new Date(scheduledDate * 1000).toLocaleString() : 'Not scheduled';
                        
                        const row = `
                            <tr class="session-row" data-id="${session.bookingId || session.booking_id}">
                                <td>${session.bookingId || session.booking_id || 'N/A'}</td>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <div class="mr-2">
                                            <i class="fas fa-user-circle text-primary"></i>
                                        </div>
                                        <div>
                                            <strong>${session.userName || session.user_fullname || session.userAccount || 'N/A'}</strong>
                                            <br><small class="text-muted">@${session.userAccount || session.user_account || 'N/A'}</small>
                                        </div>
                                    </div>
                                </td>
                                <td>
                                    <i class="fas fa-calendar-alt text-info mr-1"></i>
                                    ${scheduledDateStr}
                                </td>
                                <td>${session.sessionType || session.session_type || 'Consultation'}</td>
                                <td>
                                    <span class="badge badge-${riskClass} badge-pill">
                                        <i class="fas fa-${getRiskIcon(session.riskLevel || session.risk_level)} mr-1"></i>
                                        ${(session.riskLevel || session.risk_level || 'N/A').toUpperCase()}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge badge-${statusClass}">
                                        ${(session.bookingStatus || session.booking_status || 'PENDING').toUpperCase()}
                                    </span>
                                </td>
                                <td>
                                    <div class="btn-group" role="group">
                                        ${(session.bookingStatus || session.booking_status) === 'pending' ? `
                                            <button class="btn btn-sm btn-success" onclick="acceptSession('${session.bookingId || session.booking_id}')" title="Accept Session">
                                                <i class="fas fa-check"></i>
                                            </button>
                                            <button class="btn btn-sm btn-danger" onclick="declineSession('${session.bookingId || session.booking_id}')" title="Decline Session">
                                                <i class="fas fa-times"></i>
                                            </button>
                                        ` : ''}
                                        <button class="btn btn-sm btn-primary" onclick="viewSessionDetails('${session.bookingId || session.booking_id}')" title="View Details">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                        <button class="btn btn-sm btn-info" onclick="addSessionNotes('${session.bookingId || session.booking_id}')" title="Add Notes">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `;
                        tbody.append(row);
                    });
                } else {
                    tbody.html('<tr><td colspan="7" class="text-center text-muted"><i class="fas fa-calendar-times mr-2"></i>No sessions found</td></tr>');
                }
            })
            .catch(error => {
                console.error('❌ Error loading sessions:', error);
                tbody.html('<tr><td colspan="7" class="text-center text-danger"><i class="fas fa-exclamation-triangle mr-2"></i>Error loading sessions: ' + error.message + '</td></tr>');
            });
    }

    /**
     * Load patients
     */
    function loadPatients() {
        console.log('👥 Loading patients...');
        const tbody = $('#patientsTableBody');
        tbody.html('<tr><td colspan="7" class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>');
        
        apiFetch('/professional/booked-users')
            .then(response => response.json())
            .then(data => {
                console.log('👥 Patients data received:', data);
                tbody.empty();

                // Handle both array and object with users property
                const users = Array.isArray(data) ? data : (data.users || []);
                
                if (users && users.length > 0) {
                    users.forEach(user => {
                        const riskClass = getRiskClass(user.highestRiskLevel || user.highest_risk_level);
                        const lastSessionTs = user.lastBookingTime || user.last_booking_time;
                        const lastSessionDate = lastSessionTs ? new Date(lastSessionTs * 1000).toLocaleDateString() : 'N/A';
                        
                        const row = `
                            <tr class="patient-row" data-username="${user.userAccount || user.username}">
                                <td>
                                    <div class="d-flex align-items-center">
                                        <div class="mr-2">
                                            <i class="fas fa-user-circle text-primary"></i>
                                        </div>
                                        <div>
                                            <strong>${user.fullName || user.fullname || 'N/A'}</strong>
                                            <br><small class="text-muted">@${user.userAccount || user.username || 'N/A'}</small>
                                        </div>
                                    </div>
                                </td>
                                <td>
                                    <div>
                                        <a href="mailto:${user.email || '#'}" class="text-decoration-none">
                                            <i class="fas fa-envelope mr-1"></i>${user.email || 'N/A'}
                                        </a>
                                        <br>
                                        ${user.telephone ? `<a href="tel:${user.telephone}" class="text-decoration-none"><i class="fas fa-phone mr-1"></i>${user.telephone}</a>` : 'N/A'}
                                    </div>
                                </td>
                                <td>
                                    <i class="fas fa-map-marker-alt text-danger mr-1"></i>
                                    ${user.userLocation || (user.district || 'N/A') + ', ' + (user.province || 'N/A')}
                                </td>
                                <td>
                                    <span class="badge badge-info">
                                        <i class="fas fa-calendar-check mr-1"></i>${user.totalBookings || user.total_bookings || 0}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge badge-${riskClass} badge-pill">
                                        <i class="fas fa-${getRiskIcon(user.highestRiskLevel || user.highest_risk_level)} mr-1"></i>
                                        ${(user.highestRiskLevel || user.highest_risk_level || 'N/A').toUpperCase()}
                                    </span>
                                </td>
                                <td>
                                    <i class="fas fa-clock text-muted mr-1"></i>
                                    ${lastSessionDate}
                                </td>
                                <td>
                                    <div class="btn-group" role="group">
                                        <button class="btn btn-sm btn-primary" onclick="viewPatientProfile('${user.userAccount || user.username}')" title="View Profile">
                                            <i class="fas fa-user"></i>
                                        </button>
                                        <button class="btn btn-sm btn-success" onclick="scheduleSession('${user.userAccount || user.username}')" title="Schedule Session">
                                            <i class="fas fa-calendar-plus"></i>
                                        </button>
                                        <button class="btn btn-sm btn-info" onclick="viewPatientHistory('${user.userAccount || user.username}')" title="View History">
                                            <i class="fas fa-history"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `;
                        tbody.append(row);
                    });
                } else {
                    tbody.html('<tr><td colspan="7" class="text-center text-muted"><i class="fas fa-users-slash mr-2"></i>No patients found</td></tr>');
                }
            })
            .catch(error => {
                console.error('❌ Error loading patients:', error);
                tbody.html('<tr><td colspan="7" class="text-center text-danger"><i class="fas fa-exclamation-triangle mr-2"></i>Error loading patients: ' + error.message + '</td></tr>');
            });
    }

    /**
     * Load notifications
     */
    function loadNotifications() {
        console.log('🔔 Loading notifications...');
        const container = $('#notificationsList');
        container.html('<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading notifications...</div>');
        
        apiFetch('/professional/notifications')
            .then(response => response.json())
            .then(data => {
                console.log('🔔 Notifications data received:', data);
                container.empty();

                // Handle both array and object with notifications property
                const notifications = Array.isArray(data) ? data : (data.notifications || []);
                
                if (notifications && notifications.length > 0) {
                    notifications.forEach(notification => {
                        const isRead = notification.isRead || notification.is_read;
                        const isReadClass = isRead ? 'read' : 'unread';
                        const priority = notification.priority || 'normal';
                        const priorityClass = priority === 'high' || priority === 'urgent' ? 'danger' : priority === 'medium' ? 'warning' : 'info';
                        const createdTs = notification.createdAt || notification.created_ts || notification.created_at;
                        const createdDate = createdTs ? new Date(createdTs * 1000).toLocaleString() : 'N/A';
                        
                        const notificationHtml = `
                            <div class="alert alert-${priorityClass} alert-dismissible ${isReadClass}" data-id="${notification.id}">
                                <button type="button" class="close" onclick="markNotificationRead(${notification.id})">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                                <h5><i class="fas fa-bell mr-2"></i>${notification.title || 'Notification'}</h5>
                                <p>${notification.message || ''}</p>
                                <small class="text-muted">
                                    <i class="fas fa-clock mr-1"></i>${createdDate}
                                </small>
                            </div>
                        `;
                        container.append(notificationHtml);
                    });
                } else {
                    container.html('<div class="text-center text-muted"><i class="fas fa-bell-slash mr-2"></i>No notifications found</div>');
                }
            })
            .catch(error => {
                console.error('❌ Error loading notifications:', error);
                container.html('<div class="text-center text-danger"><i class="fas fa-exclamation-triangle mr-2"></i>Error loading notifications: ' + error.message + '</div>');
            });
    }

    /**
     * Load profile
     */
    function loadProfile() {
        console.log('👤 Loading profile...');
        
        apiFetch('/professional/profile')
            .then(response => response.json())
            .then(data => {
                console.log('👤 Profile data received:', data);
                
                // Handle both direct object and nested professional object
                const prof = data.professional || data;
                
                if (prof) {
                    // Update profile information
                    const firstName = prof.first_name || prof.firstName || '';
                    const lastName = prof.last_name || prof.lastName || '';
                    const fullName = firstName && lastName ? `${firstName} ${lastName}` : (prof.name || 'Professional');
                    
                    $('#profileName').text(fullName);
                    $('#profileRole').text(prof.specialization || 'Professional');
                    $('#profileEmail').text(prof.email || 'N/A');
                    $('#profilePhone').text(prof.phone || 'N/A');
                    $('#profileDistrict').text(prof.district || 'N/A');
                    $('#profileExperience').text(`${prof.experience_years || prof.experienceYears || 0} years`);
                    $('#profileFee').text(prof.consultation_fee || prof.consultationFee ? `RWF ${(prof.consultation_fee || prof.consultationFee || 0).toLocaleString()}` : 'N/A');
                    $('#profileBio').text(prof.bio || 'No bio available');
                    
                    // Update expertise areas
                    const expertiseList = $('#profileExpertise');
                    expertiseList.empty();
                    const expertiseAreas = prof.expertise_areas || prof.expertiseAreas || [];
                    if (Array.isArray(expertiseAreas) && expertiseAreas.length > 0) {
                        expertiseAreas.forEach(area => {
                            expertiseList.append(`<span class="badge badge-info mr-1 mb-1">${area}</span>`);
                        });
                    } else {
                        expertiseList.append('<span class="text-muted">No expertise areas specified</span>');
                    }
                    
                    // Update languages
                    const languagesList = $('#profileLanguages');
                    languagesList.empty();
                    const languages = prof.languages || [];
                    if (Array.isArray(languages) && languages.length > 0) {
                        languages.forEach(lang => {
                            languagesList.append(`<span class="badge badge-success mr-1 mb-1">${lang}</span>`);
                        });
                    } else {
                        languagesList.append('<span class="text-muted">No languages specified</span>');
                    }
                } else {
                    console.error('❌ No profile data received');
                    $('#profileName').text('Error loading profile');
                    $('#profileEmail').text('Error');
                    $('#profilePhone').text('Error');
                    $('#profileDistrict').text('Error');
                    $('#profileExperience').text('Error');
                    $('#profileFee').text('Error');
                    $('#profileBio').text('Error loading profile data');
                }
            })
            .catch(error => {
                console.error('❌ Error loading profile:', error);
                $('#profileName').text('Error loading profile');
                $('#profileEmail').text('Error: ' + error.message);
                $('#profilePhone').text('Error');
                $('#profileDistrict').text('Error');
                $('#profileExperience').text('Error');
                $('#profileFee').text('Error');
                $('#profileBio').text('Error loading profile: ' + error.message);
            });
    }

    /**
     * Load reports
     */
    function loadReports() {
        console.log('📊 Loading reports...');
        // Placeholder for reports functionality
        $('#reports-section .card-body').html('<div class="text-center text-muted"><i class="fas fa-chart-bar mr-2"></i>Reports functionality coming soon</div>');
    }

    /**
     * Initialize DataTables
     */
    function initializeDataTables() {
        // Initialize DataTables for sessions and patients tables
        if ($.fn.DataTable) {
            $('#sessionsTable').DataTable({
                responsive: true,
                processing: true,
                serverSide: false,
                pageLength: 25,
                order: [[3, 'desc']], // Sort by date
                columnDefs: [
                    { targets: [-1], orderable: false } // Actions column
                ]
            });
            
            $('#patientsTable').DataTable({
                responsive: true,
                processing: true,
                serverSide: false,
                pageLength: 25,
                order: [[5, 'desc']], // Sort by last session
                columnDefs: [
                    { targets: [-1], orderable: false } // Actions column
                ]
            });
        }
    }

    /**
     * Initialize charts
     */
    function initializeCharts() {
        // Placeholder for chart initialization
        console.log('📊 Charts initialized');
    }

    /**
     * Initialize event handlers
     */
    function initializeEventHandlers() {
        // Logout functionality
        $('#logoutBtn').on('click', function(e) {
            e.preventDefault();
            logout();
        });
        
        // Refresh dashboard button
        $('#refreshDashboardBtn').on('click', function() {
            loadDashboardData();
        });
        
        // Add any additional event handlers here
        console.log('🎯 Event handlers initialized');
    }
    
    // Global functions for button clicks
    window.refreshSessions = function() {
        console.log('🔄 Refreshing sessions...');
        loadSessions();
    };
    
    window.addNewSession = function() {
        console.log('➕ Adding new session...');
        Swal.fire('New Session', 'New session functionality coming soon', 'info');
    };

    /**
     * Logout function
     */
    function logout() {
        console.log('🚪 Logging out...');
        
        Swal.fire({
            title: 'Logout',
            text: 'Are you sure you want to logout?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes, logout!',
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                // Optional: Call backend logout endpoint
                fetch(`${API_ROOT}/logout`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }).catch(error => {
                    console.log('Backend logout call failed, continuing with client-side logout:', error);
                });
                
                // Clear localStorage
                localStorage.removeItem('aimhsa_professional');
                localStorage.removeItem('aimhsa_user');
                localStorage.removeItem('aimhsa_admin');
                
                // Show success message
                Swal.fire({
                    title: 'Logged Out!',
                    text: 'You have been successfully logged out.',
            icon: 'success',
                    timer: 2000,
                    showConfirmButton: false
        }).then(() => {
                    // Redirect to login page
                    window.location.href = '/login.html';
                });
            }
        });
    }

    /**
     * Start auto-refresh
     */
    function startAutoRefresh() {
        // Refresh dashboard data every 30 seconds
        setInterval(() => {
            if (currentSection === 'dashboard') {
                loadDashboardStats();
            }
        }, 30000);
        
        // Refresh notifications every 60 seconds
        setInterval(() => {
            if (currentSection === 'notifications') {
                loadNotifications();
            }
        }, 60000);
    }

    /**
     * Load dashboard data
     */
    function loadDashboardData() {
        console.log('🔄 Loading dashboard data...');
        loadDashboardStats();
    }

    // Utility functions
    function getRiskClass(riskLevel) {
        const classes = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'success'
        };
        return classes[riskLevel?.toLowerCase()] || 'secondary';
    }

    function getRiskIcon(riskLevel) {
        const icons = {
            'critical': 'exclamation-triangle',
            'high': 'exclamation-circle',
            'medium': 'info-circle',
            'low': 'check-circle'
        };
        return icons[riskLevel?.toLowerCase()] || 'question-circle';
    }

    function getStatusClass(status) {
        const classes = {
            'confirmed': 'success',
            'pending': 'warning',
            'declined': 'danger',
            'completed': 'info'
        };
        return classes[status?.toLowerCase()] || 'secondary';
    }

    // Global functions for button clicks
    window.acceptSession = function(bookingId) {
        console.log('✅ Accepting session:', bookingId);
        
            Swal.fire({
            title: 'Accept Session',
            html: `
                <div class="form-group">
                    <label for="acceptNotes">Acceptance Notes (Optional):</label>
                    <textarea id="acceptNotes" class="form-control" rows="3" placeholder="Add any notes about accepting this session..."></textarea>
                </div>
                <div class="form-group">
                    <label for="suggestedTime">Suggested Session Time:</label>
                    <input type="datetime-local" id="suggestedTime" class="form-control">
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: 'Accept Session',
            confirmButtonColor: '#28a745',
            preConfirm: () => {
                const notes = document.getElementById('acceptNotes').value;
                const suggestedTime = document.getElementById('suggestedTime').value;
                return { notes, suggestedTime };
            }
        }).then((result) => {
            if (result.isConfirmed) {
                apiFetch(`/professional/sessions/${bookingId}/status`, {
                    method: 'PUT',
                    body: JSON.stringify({ 
                        status: 'confirmed',
                        professional_id: currentProfessional.id || currentProfessional.professional_id,
                        notes: result.value.notes,
                        suggested_time: result.value.suggestedTime
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.ok || data.success) {
                        Swal.fire('Success!', 'Session accepted successfully', 'success');
                        loadSessions();
                    } else {
                        Swal.fire('Error!', data.error || 'Failed to accept session', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error accepting session:', error);
                    Swal.fire('Error!', 'Failed to accept session', 'error');
                });
            }
        });
    };

    window.declineSession = function(bookingId) {
        console.log('❌ Declining session:', bookingId);
        
            Swal.fire({
            title: 'Decline Session',
            html: `
                <div class="form-group">
                    <label for="declineReason">Reason for Declining:</label>
                    <select id="declineReason" class="form-control">
                        <option value="schedule_conflict">Schedule Conflict</option>
                        <option value="not_specialized">Not My Specialization</option>
                        <option value="workload_full">Workload Full</option>
                        <option value="patient_preference">Patient Preference</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="declineNotes">Additional Notes:</label>
                    <textarea id="declineNotes" class="form-control" rows="3" placeholder="Provide additional details..."></textarea>
                </div>
            `,
                showCancelButton: true,
            confirmButtonText: 'Decline Session',
            confirmButtonColor: '#dc3545',
            preConfirm: () => {
                const reason = document.getElementById('declineReason').value;
                const notes = document.getElementById('declineNotes').value;
                
                if (!reason) {
                    Swal.showValidationMessage('Please select a reason for declining');
                    return false;
                }
                
                return { reason, notes };
            }
            }).then((result) => {
                if (result.isConfirmed) {
                apiFetch(`/professional/sessions/${bookingId}/status`, {
                    method: 'PUT',
                    body: JSON.stringify({ 
                        status: 'declined',
                        professional_id: currentProfessional.id || currentProfessional.professional_id,
                        reason: result.value.reason,
                        notes: result.value.notes
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.ok || data.success) {
                        Swal.fire('Declined!', 'Session declined successfully', 'success');
                        loadSessions();
                    } else {
                        Swal.fire('Error!', data.error || 'Failed to decline session', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error declining session:', error);
                    Swal.fire('Error!', 'Failed to decline session', 'error');
                });
            }
        });
    };

    window.viewSessionDetails = function(bookingId) {
        console.log('👁️ Viewing session details:', bookingId);
        
        // Find the session data from the current sessions
        const sessionRow = $(`.session-row[data-id="${bookingId}"]`);
        if (sessionRow.length === 0) {
            Swal.fire('Error', 'Session not found', 'error');
            return;
        }
        
        // Extract session data from the row
        const userFullname = sessionRow.find('td:first-child strong').text();
        const username = sessionRow.find('td:first-child small').text().replace('@', '');
        const riskLevel = sessionRow.find('td:nth-child(2) span').text();
        const status = sessionRow.find('td:nth-child(3) span').text();
        const date = sessionRow.find('td:nth-child(4)').text();
        const location = sessionRow.find('td:nth-child(5)').text();
        
        Swal.fire({
            title: 'Session Details',
            html: `
                <div class="session-details">
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong>Patient:</strong><br>
                            ${userFullname}<br>
                            <small class="text-muted">${username}</small>
                        </div>
                        <div class="col-6">
                            <strong>Risk Level:</strong><br>
                            <span class="badge badge-${getRiskClass(riskLevel.toLowerCase())}">${riskLevel}</span>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong>Status:</strong><br>
                            <span class="badge badge-${getStatusClass(status.toLowerCase())}">${status}</span>
                        </div>
                        <div class="col-6">
                            <strong>Date:</strong><br>
                            ${date}
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-12">
                            <strong>Location:</strong><br>
                            ${location}
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-12">
                            <strong>Actions:</strong><br>
                            <div class="btn-group mt-2" role="group">
                                <button class="btn btn-sm btn-primary" onclick="contactPatient('${username}')">
                                    <i class="fas fa-envelope"></i> Contact Patient
                                </button>
                                <button class="btn btn-sm btn-info" onclick="scheduleFollowUp('${bookingId}')">
                                    <i class="fas fa-calendar-plus"></i> Schedule Follow-up
                                </button>
                                <button class="btn btn-sm btn-warning" onclick="viewRiskAssessment('${bookingId}')">
                                    <i class="fas fa-chart-line"></i> Risk Assessment
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `,
            width: '600px',
            showCloseButton: true,
            showConfirmButton: false
        });
    };

    window.addSessionNotes = function(bookingId) {
        console.log('📝 Adding session notes:', bookingId);
        
        Swal.fire({
            title: 'Add Session Notes',
            html: `
                <div class="form-group">
                    <label for="sessionNotes">Session Notes:</label>
                    <textarea id="sessionNotes" class="form-control" rows="4" placeholder="Enter session notes..."></textarea>
                </div>
                <div class="form-group">
                    <label for="treatmentPlan">Treatment Plan:</label>
                    <textarea id="treatmentPlan" class="form-control" rows="3" placeholder="Enter treatment plan..."></textarea>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: 'Save Notes',
            preConfirm: () => {
                const notes = document.getElementById('sessionNotes').value;
                const treatmentPlan = document.getElementById('treatmentPlan').value;
                
                if (!notes.trim()) {
                    Swal.showValidationMessage('Please enter session notes');
                    return false;
                }
                
                return { notes, treatmentPlan };
            }
        }).then((result) => {
            if (result.isConfirmed) {
                apiFetch(`/professional/sessions/${bookingId}/notes`, {
                    method: 'POST',
                    body: JSON.stringify({
                        professional_id: currentProfessional.id || currentProfessional.professional_id,
                        ...result.value
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.ok || data.success) {
                        Swal.fire('Success!', 'Session notes added successfully', 'success');
                        loadSessions();
                    } else {
                        Swal.fire('Error!', data.error || 'Failed to add notes', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error adding notes:', error);
                    Swal.fire('Error!', 'Failed to add notes', 'error');
                });
            }
        });
    };

    window.markNotificationRead = function(notificationId) {
        console.log('✅ Marking notification as read:', notificationId);
        
        apiFetch(`/professional/notifications/${notificationId}/read`, {
            method: 'PUT'
        })
        .then(response => response.json())
        .then(data => {
            if (data.ok || data.success) {
                $(`.alert[data-id="${notificationId}"]`).removeClass('unread').addClass('read');
                loadDashboardStats(); // Refresh notification count
                loadNotifications(); // Refresh notifications list
            }
        })
        .catch(error => {
            console.error('Error marking notification as read:', error);
        });
    };

    window.markAllAsRead = function() {
        console.log('✅ Marking all notifications as read');
        // Placeholder for mark all as read functionality
        Swal.fire('Mark All Read', 'Mark all as read functionality coming soon', 'info');
    };

    window.refreshPatients = function() {
        console.log('🔄 Refreshing patients...');
        loadPatients();
    };

    window.viewPatientProfile = function(username) {
        console.log('👤 Viewing patient profile:', username);
        Swal.fire('Patient Profile', `Patient profile for ${username} coming soon`, 'info');
    };

    window.scheduleSession = function(username) {
        console.log('📅 Scheduling session for:', username);
        Swal.fire('Schedule Session', `Schedule session for ${username} coming soon`, 'info');
    };

    window.viewPatientHistory = function(username) {
        console.log('📋 Viewing patient history:', username);
        
        // Show loading state
        Swal.fire({
            title: 'Loading Patient History',
            html: 'Please wait while we fetch the conversation history...',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
        
        // Fetch patient history
        apiFetch(`/professional/patient-history/${encodeURIComponent(username)}`)
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Failed to load patient history');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('📋 Patient history data:', data);
                
                // Format conversations for display
                let conversationHtml = '';
                if (data.conversations && data.conversations.length > 0) {
                    data.conversations.forEach((conv, index) => {
                        const convDate = new Date(conv.timestamp * 1000).toLocaleString();
                        const messageCount = conv.message_count || conv.messages?.length || 0;
                        
                        conversationHtml += `
                            <div class="conversation-item" style="margin-bottom: 20px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #f9f9f9;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <h4 style="margin: 0; color: #2c5aa0; font-size: 16px;">
                                        <i class="fas fa-comments mr-2"></i>${conv.preview || 'Conversation'}
                                    </h4>
                                    <div style="font-size: 12px; color: #666;">
                                        <i class="fas fa-calendar mr-1"></i>${convDate}
                                        <span style="margin-left: 10px;">
                                            <i class="fas fa-comment-dots mr-1"></i>${messageCount} messages
                                        </span>
                                    </div>
                                </div>
                                <div class="messages-container" style="max-height: 300px; overflow-y: auto; padding: 10px; background: white; border-radius: 4px;">
                                    ${conv.messages && conv.messages.length > 0 ? conv.messages.map((msg, msgIndex) => {
                                        const msgDate = new Date(msg.timestamp * 1000).toLocaleTimeString();
                                        const isUser = msg.role === 'user';
                                        return `
                                            <div style="margin-bottom: 12px; padding: 10px; border-radius: 6px; ${isUser ? 'background: #e3f2fd; margin-left: 20px;' : 'background: #f5f5f5; margin-right: 20px;'}">
                                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                                    <strong style="color: ${isUser ? '#1976d2' : '#666'};">
                                                        ${isUser ? '<i class="fas fa-user mr-1"></i>Patient' : '<i class="fas fa-robot mr-1"></i>AIMHSA'}
                                                    </strong>
                                                    <span style="font-size: 11px; color: #999;">${msgDate}</span>
                                                </div>
                                                <div style="color: #333; white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(msg.content)}</div>
                                            </div>
                                        `;
                                    }).join('') : '<p style="color: #999; font-style: italic;">No messages in this conversation</p>'}
                                </div>
                            </div>
                        `;
                    });
                } else {
                    conversationHtml = `
                        <div style="text-align: center; padding: 40px; color: #999;">
                            <i class="fas fa-comments" style="font-size: 48px; margin-bottom: 15px; opacity: 0.5;"></i>
                            <p>No conversation history found for this patient.</p>
                        </div>
                    `;
                }
                
                // Show the modal with conversation history
                Swal.fire({
                    title: `Patient History: ${username}`,
                    html: `
                        <div style="text-align: left; max-height: 70vh; overflow-y: auto;">
                            <div style="margin-bottom: 15px; padding: 10px; background: #e3f2fd; border-radius: 6px;">
                                <strong><i class="fas fa-info-circle mr-2"></i>Total Conversations:</strong> ${data.total_conversations || 0}
                            </div>
                            ${conversationHtml}
                        </div>
                    `,
                    width: '900px',
                    showCloseButton: true,
                    showConfirmButton: true,
                    confirmButtonText: 'Close',
                    confirmButtonColor: '#2c5aa0',
                    customClass: {
                        popup: 'patient-history-modal'
                    }
                });
            })
            .catch(error => {
                console.error('❌ Error loading patient history:', error);
                Swal.fire({
                    title: 'Error',
                    text: error.message || 'Failed to load patient history',
                    icon: 'error',
                    confirmButtonText: 'OK',
                    confirmButtonColor: '#dc3545'
                });
            });
    };
    
    // Helper function to escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    window.addNewSession = function() {
        console.log('➕ Adding new session');
        Swal.fire('New Session', 'New session functionality coming soon', 'info');
    };

    window.editProfile = function() {
        console.log('✏️ Editing profile');
        Swal.fire('Edit Profile', 'Profile editing functionality coming soon', 'info');
    };

    // New enhanced functions
    window.contactPatient = function(username) {
        console.log('📧 Contacting patient:', username);
        
        Swal.fire({
            title: 'Contact Patient',
            html: `
                <div class="form-group">
                    <label for="messageType">Message Type:</label>
                    <select id="messageType" class="form-control">
                        <option value="appointment_reminder">Appointment Reminder</option>
                        <option value="follow_up">Follow-up Check</option>
                        <option value="treatment_update">Treatment Update</option>
                        <option value="emergency">Emergency Contact</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="patientMessage">Message:</label>
                    <textarea id="patientMessage" class="form-control" rows="4" placeholder="Type your message to the patient..."></textarea>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: 'Send Message',
            confirmButtonColor: '#007bff',
            preConfirm: () => {
                const messageType = document.getElementById('messageType').value;
                const message = document.getElementById('patientMessage').value;
                
                if (!message.trim()) {
                    Swal.showValidationMessage('Please enter a message');
                    return false;
                }
                
                return { messageType, message };
            }
        }).then((result) => {
            if (result.isConfirmed) {
                // Simulate sending message
                Swal.fire('Message Sent!', `Message sent to ${username}`, 'success');
            }
        });
    };

    window.scheduleFollowUp = function(bookingId) {
        console.log('📅 Scheduling follow-up for:', bookingId);
        
        Swal.fire({
            title: 'Schedule Follow-up',
            html: `
                <div class="form-group">
                    <label for="followUpDate">Follow-up Date:</label>
                    <input type="date" id="followUpDate" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="followUpTime">Follow-up Time:</label>
                    <input type="time" id="followUpTime" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="followUpType">Follow-up Type:</label>
                    <select id="followUpType" class="form-control">
                        <option value="phone_call">Phone Call</option>
                        <option value="video_session">Video Session</option>
                        <option value="in_person">In-Person Session</option>
                        <option value="text_check">Text Check-in</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="followUpNotes">Notes:</label>
                    <textarea id="followUpNotes" class="form-control" rows="3" placeholder="Add any notes for the follow-up..."></textarea>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: 'Schedule Follow-up',
            confirmButtonColor: '#28a745',
            preConfirm: () => {
                const date = document.getElementById('followUpDate').value;
                const time = document.getElementById('followUpTime').value;
                const type = document.getElementById('followUpType').value;
                const notes = document.getElementById('followUpNotes').value;
                
                if (!date || !time) {
                    Swal.showValidationMessage('Please select both date and time');
                    return false;
                }
                
                return { date, time, type, notes };
            }
        }).then((result) => {
            if (result.isConfirmed) {
                Swal.fire('Follow-up Scheduled!', 'Follow-up session has been scheduled', 'success');
            }
        });
    };

    window.viewRiskAssessment = function(bookingId) {
        console.log('📊 Viewing risk assessment for:', bookingId);
        
        Swal.fire({
            title: 'Risk Assessment Details',
            html: `
                <div class="risk-assessment">
                    <div class="alert alert-warning">
                        <h5><i class="fas fa-exclamation-triangle"></i> Risk Assessment</h5>
                        <p>Detailed risk assessment analysis will be displayed here.</p>
                    </div>
                    <div class="row">
                        <div class="col-6">
                            <strong>Risk Score:</strong> 0.85<br>
                            <strong>Risk Level:</strong> High<br>
                            <strong>Indicators:</strong> Depression, Isolation
                        </div>
                        <div class="col-6">
                            <strong>Assessment Date:</strong> Today<br>
                            <strong>Assessor:</strong> AI System<br>
                            <strong>Confidence:</strong> 92%
                        </div>
                    </div>
                    <div class="mt-3">
                        <strong>Recommended Actions:</strong>
                        <ul>
                            <li>Immediate professional intervention</li>
                            <li>Regular check-ins</li>
                            <li>Consider medication evaluation</li>
                        </ul>
                    </div>
                </div>
            `,
            width: '700px',
            showCloseButton: true,
            showConfirmButton: false
        });
    };

})();