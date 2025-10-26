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
        if (loc.port === '8000') {
            apiRoot = `${loc.protocol}//${loc.hostname}:7860`;
        } else if (loc.port === '7860' || loc.port === '') {
            apiRoot = loc.origin;
        } else {
            apiRoot = 'https://fezaflora-aimhsa.hf.space';
        }
    } catch (_) {
        apiRoot = 'https://fezaflora-aimhsa.hf.space';
    }
    const API_ROOT = apiRoot;

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
        
        fetch(`${API_ROOT}/professional/dashboard-stats?id=${currentProfessional.id}`)
            .then(response => response.json())
            .then(data => {
                console.log('📊 Dashboard stats received:', data);
                
                // Update KPI cards
                $('#totalSessions').text(data.total_sessions || 0);
                $('#unreadNotifications').text(data.unread_notifications || 0);
                $('#upcomingToday').text(data.today_sessions || 0);
                $('#highRiskSessions').text(data.high_risk_sessions || 0);
                
                // Update notification badge
                $('#notificationCount').text(data.unread_notifications || 0);
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
        
        fetch(`${API_ROOT}/professional/sessions?id=${currentProfessional.id}`)
            .then(response => response.json())
            .then(data => {
                console.log('📅 Sessions data received:', data);
                tbody.empty();
                
                if (data.sessions && data.sessions.length > 0) {
                    data.sessions.forEach(session => {
                        const riskClass = getRiskClass(session.risk_level);
                        const statusClass = getStatusClass(session.booking_status);
                        const createdDate = new Date(session.created_ts * 1000).toLocaleDateString();
                        
                        const row = `
                            <tr class="session-row" data-id="${session.booking_id}">
                                <td>
                                    <div class="d-flex align-items-center">
                                        <div class="mr-2">
                                            <i class="fas fa-user-circle text-primary"></i>
                                        </div>
                                        <div>
                                            <strong>${session.user_fullname || 'N/A'}</strong>
                                            <br><small class="text-muted">@${session.user_account}</small>
                                        </div>
                                    </div>
                                </td>
                                <td>
                                    <span class="badge badge-${riskClass} badge-pill">
                                        <i class="fas fa-${getRiskIcon(session.risk_level)} mr-1"></i>
                                        ${session.risk_level?.toUpperCase() || 'N/A'}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge badge-${statusClass}">
                                        ${session.booking_status?.toUpperCase() || 'PENDING'}
                                    </span>
                                </td>
                                <td>
                                    <i class="fas fa-calendar-alt text-info mr-1"></i>
                                    ${createdDate}
                                </td>
                                <td>
                                    ${session.user_location || 'N/A'}
                                </td>
                                <td>
                                    ${session.session_notes ? 'Yes' : 'No'}
                                </td>
                                <td>
                                    <div class="btn-group" role="group">
                                        ${session.booking_status === 'pending' ? `
                                            <button class="btn btn-sm btn-success" onclick="acceptSession('${session.booking_id}')" title="Accept Session">
                                                <i class="fas fa-check"></i>
                                            </button>
                                            <button class="btn btn-sm btn-danger" onclick="declineSession('${session.booking_id}')" title="Decline Session">
                                                <i class="fas fa-times"></i>
                                            </button>
                                        ` : ''}
                                        <button class="btn btn-sm btn-primary" onclick="viewSessionDetails('${session.booking_id}')" title="View Details">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                        <button class="btn btn-sm btn-info" onclick="addSessionNotes('${session.booking_id}')" title="Add Notes">
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
                tbody.html('<tr><td colspan="7" class="text-center text-danger"><i class="fas fa-exclamation-triangle mr-2"></i>Error loading sessions</td></tr>');
            });
    }

    /**
     * Load patients
     */
    function loadPatients() {
        console.log('👥 Loading patients...');
        const tbody = $('#patientsTableBody');
        tbody.html('<tr><td colspan="7" class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>');
        
        fetch(`${API_ROOT}/professional/users?id=${currentProfessional.id}`)
            .then(response => response.json())
            .then(data => {
                console.log('👥 Patients data received:', data);
                tbody.empty();
                
                if (data.users && data.users.length > 0) {
                    data.users.forEach(user => {
                        const riskClass = getRiskClass(user.highest_risk_level);
                        const lastSessionDate = user.last_session_date ? new Date(user.last_session_date * 1000).toLocaleDateString() : 'N/A';
                        
                        const row = `
                            <tr class="patient-row" data-username="${user.username}">
                                <td>
                                    <div class="d-flex align-items-center">
                                        <div class="mr-2">
                                            <i class="fas fa-user-circle text-primary"></i>
                                        </div>
                                        <div>
                                            <strong>${user.fullname || 'N/A'}</strong>
                                            <br><small class="text-muted">@${user.username}</small>
                                        </div>
                                    </div>
                                </td>
                                <td>
                                    <div>
                                        <a href="mailto:${user.email}" class="text-decoration-none">
                                            <i class="fas fa-envelope mr-1"></i>${user.email || 'N/A'}
                                        </a>
                                        <br>
                                        ${user.telephone ? `<a href="tel:${user.telephone}" class="text-decoration-none"><i class="fas fa-phone mr-1"></i>${user.telephone}</a>` : 'N/A'}
                                    </div>
                                </td>
                                <td>
                                    <i class="fas fa-map-marker-alt text-danger mr-1"></i>
                                    ${user.district || 'N/A'}, ${user.province || 'N/A'}
                                </td>
                                <td>
                                    <span class="badge badge-info">
                                        <i class="fas fa-calendar-check mr-1"></i>${user.total_sessions || 0}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge badge-${riskClass} badge-pill">
                                        <i class="fas fa-${getRiskIcon(user.highest_risk_level)} mr-1"></i>
                                        ${user.highest_risk_level?.toUpperCase() || 'N/A'}
                                    </span>
                                </td>
                                <td>
                                    <i class="fas fa-clock text-muted mr-1"></i>
                                    ${lastSessionDate}
                                </td>
                                <td>
                                    <div class="btn-group" role="group">
                                        <button class="btn btn-sm btn-primary" onclick="viewPatientProfile('${user.username}')" title="View Profile">
                                            <i class="fas fa-user"></i>
                                        </button>
                                        <button class="btn btn-sm btn-success" onclick="scheduleSession('${user.username}')" title="Schedule Session">
                                            <i class="fas fa-calendar-plus"></i>
                                        </button>
                                        <button class="btn btn-sm btn-info" onclick="viewPatientHistory('${user.username}')" title="View History">
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
                tbody.html('<tr><td colspan="7" class="text-center text-danger"><i class="fas fa-exclamation-triangle mr-2"></i>Error loading patients</td></tr>');
            });
    }

    /**
     * Load notifications
     */
    function loadNotifications() {
        console.log('🔔 Loading notifications...');
        const container = $('#notificationsList');
        container.html('<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading notifications...</div>');
        
        fetch(`${API_ROOT}/professional/notifications?id=${currentProfessional.id}`)
            .then(response => response.json())
            .then(data => {
                console.log('🔔 Notifications data received:', data);
                container.empty();
                
                if (data.notifications && data.notifications.length > 0) {
                    data.notifications.forEach(notification => {
                        const isRead = notification.is_read ? 'read' : 'unread';
                        const priorityClass = notification.priority === 'high' ? 'danger' : notification.priority === 'medium' ? 'warning' : 'info';
                        const createdDate = new Date(notification.created_ts * 1000).toLocaleString();
                        
                        const notificationHtml = `
                            <div class="alert alert-${priorityClass} alert-dismissible ${isRead}" data-id="${notification.id}">
                                <button type="button" class="close" onclick="markNotificationRead(${notification.id})">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                                <h5><i class="fas fa-bell mr-2"></i>${notification.title}</h5>
                                <p>${notification.message}</p>
                                <small class="text-muted">
                                    <i class="fas fa-clock mr-1"></i>${createdDate}
                                    ${notification.user_account ? ` | <i class="fas fa-user mr-1"></i>${notification.user_account}` : ''}
                                    ${notification.risk_level ? ` | <i class="fas fa-exclamation-triangle mr-1"></i>${notification.risk_level.toUpperCase()}` : ''}
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
                container.html('<div class="text-center text-danger"><i class="fas fa-exclamation-triangle mr-2"></i>Error loading notifications</div>');
            });
    }

    /**
     * Load profile
     */
    function loadProfile() {
        console.log('👤 Loading profile...');
        
        fetch(`${API_ROOT}/professional/profile?id=${currentProfessional.id}`)
            .then(response => response.json())
            .then(data => {
                console.log('👤 Profile data received:', data);
                
                if (data.professional) {
                    const prof = data.professional;
                    
                    // Update profile information
                    $('#profileName').text(`${prof.first_name} ${prof.last_name}`);
                    $('#profileRole').text(prof.specialization);
                    $('#profileEmail').text(prof.email);
                    $('#profilePhone').text(prof.phone || 'N/A');
                    $('#profileSpecialization').text(prof.specialization);
                    $('#profileDistrict').text(prof.district || 'N/A');
                    $('#profileExperience').text(`${prof.experience_years || 0} years`);
                    $('#profileFee').text(prof.consultation_fee ? `RWF ${prof.consultation_fee.toLocaleString()}` : 'N/A');
                    $('#profileBio').text(prof.bio || 'No bio available');
                    
                    // Update expertise areas
                    const expertiseList = $('#profileExpertise');
                    expertiseList.empty();
                    if (prof.expertise_areas && prof.expertise_areas.length > 0) {
                        prof.expertise_areas.forEach(area => {
                            expertiseList.append(`<span class="badge badge-info mr-1 mb-1">${area}</span>`);
                        });
                    } else {
                        expertiseList.append('<span class="text-muted">No expertise areas specified</span>');
                    }
                    
                    // Update languages
                    const languagesList = $('#profileLanguages');
                    languagesList.empty();
                    if (prof.languages && prof.languages.length > 0) {
                        prof.languages.forEach(lang => {
                            languagesList.append(`<span class="badge badge-success mr-1 mb-1">${lang}</span>`);
                        });
                    } else {
                        languagesList.append('<span class="text-muted">No languages specified</span>');
                    }
                }
            })
            .catch(error => {
                console.error('❌ Error loading profile:', error);
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
        
        // Add any additional event handlers here
        console.log('🎯 Event handlers initialized');
    }

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
                fetch(`${API_ROOT}/professional/sessions/${bookingId}/status`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        status: 'accepted',
                        notes: result.value.notes,
                        suggested_time: result.value.suggestedTime
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.ok) {
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
                fetch(`${API_ROOT}/professional/sessions/${bookingId}/status`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        status: 'declined',
                        reason: result.value.reason,
                        notes: result.value.notes
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.ok) {
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
                fetch(`${API_ROOT}/professional/sessions/${bookingId}/notes`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(result.value)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.ok) {
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
        
        fetch(`${API_ROOT}/professional/notifications/${notificationId}/read`, {
            method: 'PUT'
        })
        .then(response => response.json())
        .then(data => {
            if (data.ok) {
                $(`.alert[data-id="${notificationId}"]`).removeClass('unread').addClass('read');
                loadDashboardStats(); // Refresh notification count
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
        Swal.fire('Patient History', `Patient history for ${username} coming soon`, 'info');
    };

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