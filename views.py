from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from . import db
from .models import User, Role, Task, LeaveRequest, Announcement
from .auth import role_required
from flask import current_app

views = Blueprint('views', __name__)

@views.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for(f'views.{current_user.role.name.lower()}_page'))
    return redirect(url_for('auth.login'))

@views.route('/admin')
@login_required
@role_required(['Admin'])
def admin_page():
    users = User.query.all()
    roles = Role.query.all()
    
    # Get the current month's first day
    current_month = datetime.now().replace(day=1)
    
    # Count users registered this month
    monthly_registrations = sum(1 for user in users if user.registration_date and user.registration_date >= current_month)
    
    return render_template('Admin/Admin_Page.html', 
                          users=users, 
                          roles=roles,
                          monthly_registrations=monthly_registrations)

# Add this function to your views.py file
def get_user_name(user_id):
    """Helper function to get a user's full name by their ID"""
    user = User.query.get(user_id)
    if user:
        return f"{user.first_name} {user.last_name}"
    return "Unknown User"

@views.route('/manager')
@login_required
@role_required(['Manager'])
def manager_page():
    # Get team members (employees assigned to this manager)
    team_members = User.query.filter_by(role_id=Role.query.filter_by(name='Employee').first().id).all()
    
    # Get tasks assigned by this manager
    tasks = Task.query.filter_by(created_by=current_user.person_id).all()
    
    # Count tasks by status
    ongoing_tasks_count = Task.query.filter_by(
        created_by=current_user.person_id, 
        status='In Progress'
    ).count()
    
    completed_tasks_count = Task.query.filter_by(
        created_by=current_user.person_id, 
        status='Completed'
    ).count()
    
    # Get pending leave requests
    pending_leave_requests = LeaveRequest.query.filter_by(
        status='Pending'
    ).all()
    
    # Count pending leave requests
    pending_leave_count = len(pending_leave_requests)
    
    # Get team announcements
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    
    return render_template('Manager/Manager_Page.html', 
                          team_members=team_members,
                          team_count=len(team_members),
                          tasks=tasks,
                          ongoing_tasks_count=ongoing_tasks_count,
                          completed_tasks_count=completed_tasks_count,
                          pending_leave_requests=pending_leave_requests,
                          pending_leave_count=pending_leave_count,
                          announcements=announcements,
                          get_user_name=get_user_name)  # Add this line

# Add this to your views.py file
@views.route('/employee')
@login_required
@role_required(['Employee'])
def employee_page():
    # Get employee's tasks
    tasks = Task.query.filter_by(assigned_to=current_user.person_id).all()
    
    # Get announcements
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    
    return render_template('Employee/Employee_Page.html', 
                          tasks=tasks,
                          announcements=announcements)

@views.route('/submit_leave_request', methods=['POST'])
@login_required
@role_required(['Employee'])
def submit_leave_request():
    leave_type = request.form.get('leave_type')
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    reason = request.form.get('reason')
    
    # Create new leave request
    new_leave_request = LeaveRequest(
        user_id=current_user.person_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status='Pending'
    )
    
    try:
        db.session.add(new_leave_request)
        db.session.commit()
        flash('คำขอลาของคุณได้ถูกส่งเรียบร้อยแล้ว กรุณารอการอนุมัติ', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาดในการส่งคำขอลา: {str(e)}', 'danger')
    
    return redirect(url_for('views.employee_page'))

@views.route('/get_task_details/<int:task_id>', methods=['GET'])
@login_required
@role_required(['Employee'])
def get_task_details(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Make sure the employee can only access their own tasks
    if task.assigned_to != current_user.person_id:
        return jsonify({'status': 'error', 'message': 'คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้'}), 403
    
    creator = User.query.get(task.created_by)
    creator_name = f"{creator.first_name} {creator.last_name}" if creator else "ไม่ระบุ"
    
    return jsonify({
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_by': creator_name,
        'due_date': task.due_date.strftime('%Y-%m-%d'),
        'created_at': task.created_at.strftime('%Y-%m-%d %H:%M'),
        'attachment': task.attachment
    })

@views.route('/update_task_status/<int:task_id>', methods=['POST'])
@login_required
@role_required(['Employee'])
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Make sure the employee can only update their own tasks
    if task.assigned_to != current_user.person_id:
        return jsonify({'status': 'error', 'message': 'คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้'}), 403
    
    new_status = request.form.get('status')
    
    # Validate status values
    if new_status not in ['Pending', 'In Progress', 'Completed']:
        return jsonify({'status': 'error', 'message': 'สถานะไม่ถูกต้อง'}), 400
    
    try:
        task.status = new_status
        task.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'อัพเดทสถานะเรียบร้อยแล้ว'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@views.route('/get_leave_balance', methods=['GET'])
@login_required
@role_required(['Employee'])
def get_leave_balance():
    # This would typically come from a proper leave tracking system
    # For demonstration, we'll use a simple calculation
    
    # Count approved leave days in current year
    current_year = datetime.now().year
    year_start = datetime(current_year, 1, 1).date()
    year_end = datetime(current_year, 12, 31).date()
    
    leave_requests = LeaveRequest.query.filter(
        LeaveRequest.user_id == current_user.person_id,
        LeaveRequest.status == 'Approved',
        LeaveRequest.start_date >= year_start,
        LeaveRequest.end_date <= year_end
    ).all()
    
    # Calculate used days
    sick_leave_used = 0
    vacation_leave_used = 0
    personal_leave_used = 0
    
    for leave in leave_requests:
        days = (leave.end_date - leave.start_date).days + 1
        if leave.leave_type == 'Sick':
            sick_leave_used += days
        elif leave.leave_type == 'Vacation':
            vacation_leave_used += days
        elif leave.leave_type == 'Personal':
            personal_leave_used += days
    
    # Define total available days (could come from company policy or user settings)
    sick_leave_total = 30
    vacation_leave_total = 10
    personal_leave_total = 5
    
    return jsonify({
        'sick_leave': {
            'used': sick_leave_used,
            'total': sick_leave_total,
            'remaining': sick_leave_total - sick_leave_used
        },
        'vacation_leave': {
            'used': vacation_leave_used,
            'total': vacation_leave_total,
            'remaining': vacation_leave_total - vacation_leave_used
        },
        'personal_leave': {
            'used': personal_leave_used,
            'total': personal_leave_total,
            'remaining': personal_leave_total - personal_leave_used
        }
    })

@views.route('/get_announcements', methods=['GET'])
@login_required
def get_announcements():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category = request.args.get('category', None)
    
    query = Announcement.query.order_by(Announcement.created_at.desc())
    
    if category and category != 'All':
        query = query.filter_by(category=category)
    
    announcements = query.paginate(page=page, per_page=per_page, error_out=False)
    
    result = {
        'items': [],
        'total': announcements.total,
        'pages': announcements.pages,
        'current_page': announcements.page
    }
    
    for announcement in announcements.items:
        creator = User.query.get(announcement.created_by)
        creator_name = f"{creator.first_name} {creator.last_name}" if creator else "ไม่ระบุ"
        
        result['items'].append({
            'id': announcement.id,
            'title': announcement.title,
            'content': announcement.content,
            'category': announcement.category,
            'created_by': creator_name,
            'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    
    return jsonify(result)

@views.route('/noposition')
@login_required
@role_required(['NoPosition'])
def noposition_page():
    return render_template('NoPosition/None_Page.html')

@views.route('/update_user', methods=['POST'])
@login_required
@role_required(['Admin'])
def update_user():
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    # Update user information
    user.first_name = request.form.get('first_name')
    user.last_name = request.form.get('last_name')
    user.thai_first_name = request.form.get('thai_first_name')
    user.thai_last_name = request.form.get('thai_last_name')
    user.email = request.form.get('email')
    user.phone_number = request.form.get('phone_number')
    user.address = request.form.get('address')
    user.city = request.form.get('city')
    user.country = request.form.get('country')
    user.postal_code = request.form.get('postal_code')
    user.username = request.form.get('username')
    user.role_id = request.form.get('role_id')
    user.status = request.form.get('status')
    user.updated_at = datetime.utcnow()
    
    # Save changes
    try:
        db.session.commit()
        # For AJAX requests, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'success', 'message': f'User {user.username} has been updated successfully'})
        # For normal form submissions, redirect with flash message
        flash(f'User {user.username} has been updated successfully', 'success')
        return redirect(url_for('views.admin_page'))
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': str(e)}), 500
        flash(f'Error updating user: {str(e)}', 'danger')
        return redirect(url_for('views.admin_page'))

@views.route('/delete_user', methods=['POST'])
@login_required
@role_required(['Admin'])
def delete_user():
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('views.admin_page'))
    
    # Don't allow deleting yourself
    if int(user_id) == current_user.person_id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('views.admin_page'))
    
    # Store username for the success message
    username = user.username
    
    try:
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {username} has been deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('views.admin_page'))

# New routes for manager functionality

@views.route('/create_task', methods=['POST'])
@login_required
@role_required(['Manager'])
def create_task():
    title = request.form.get('title')
    assigned_to = request.form.get('assigned_to')
    due_date = request.form.get('due_date')
    priority = request.form.get('priority')
    description = request.form.get('description')
    
    # Handle file upload if provided
    attachment_path = None
    if 'attachment' in request.files and request.files['attachment'].filename != '':
        attachment = request.files['attachment']
        filename = secure_filename(attachment.filename)
        attachment_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'tasks')
        
        # Create directory if it doesn't exist
        os.makedirs(attachment_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(attachment_dir, filename)
        attachment.save(file_path)
        attachment_path = f'/static/uploads/tasks/{filename}'
    
    # Create new task
    new_task = Task(
        title=title,
        description=description,
        assigned_to=assigned_to,
        created_by=current_user.person_id,
        due_date=datetime.strptime(due_date, '%Y-%m-%d'),
        priority=priority,
        status='Pending',
        attachment=attachment_path
    )
    
    try:
        db.session.add(new_task)
        db.session.commit()
        flash(f'Task "{title}" has been assigned successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating task: {str(e)}', 'danger')
    
    return redirect(url_for('views.manager_page', _anchor='tasks-section'))

@views.route('/approve_leave/<int:request_id>', methods=['POST'])
@login_required
@role_required(['Manager'])
def approve_leave(request_id):
    leave_request = LeaveRequest.query.get_or_404(request_id)
    leave_request.status = 'Approved'
    leave_request.approved_by = current_user.person_id
    leave_request.approved_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Leave request approved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving leave request: {str(e)}', 'danger')
    
    return redirect(url_for('views.manager_page', _anchor='leave-section'))

@views.route('/reject_leave/<int:request_id>', methods=['POST'])
@login_required
@role_required(['Manager'])
def reject_leave(request_id):
    leave_request = LeaveRequest.query.get_or_404(request_id)
    leave_request.status = 'Rejected'
    leave_request.approved_by = current_user.person_id
    leave_request.approved_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Leave request rejected', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting leave request: {str(e)}', 'danger')
    
    return redirect(url_for('views.manager_page', _anchor='leave-section'))

@views.route('/create_announcement', methods=['POST'])
@login_required
@role_required(['Manager', 'Admin'])
def create_announcement():
    title = request.form.get('title')
    category = request.form.get('category')
    content = request.form.get('content')
    
    new_announcement = Announcement(
        title=title,
        category=category,
        content=content,
        created_by=current_user.person_id
    )
    
    try:
        db.session.add(new_announcement)
        db.session.commit()
        flash('Announcement posted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating announcement: {str(e)}', 'danger')
    
    return redirect(url_for('views.manager_page', _anchor='announcements-section'))

@views.route('/delete_announcement/<int:announcement_id>', methods=['POST'])
@login_required
@role_required(['Manager', 'Admin'])
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    
    # Only creator or admin can delete
    if announcement.created_by != current_user.person_id and current_user.role.name != 'Admin':
        flash('You do not have permission to delete this announcement', 'danger')
        return redirect(url_for('views.manager_page', _anchor='announcements-section'))
    
    try:
        db.session.delete(announcement)
        db.session.commit()
        flash('Announcement deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting announcement: {str(e)}', 'danger')
    
    return redirect(url_for('views.manager_page', _anchor='announcements-section'))

@views.route('/get_team_data', methods=['GET'])
@login_required
@role_required(['Manager'])
def get_team_data():
    # This endpoint is for AJAX requests to get team statistics
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # Get attendance data for the chart
    attendance_data = {
        'labels': [],
        'present': [],
        'absent': []
    }
    
    # Generate dates for the past 7 days
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        attendance_data['labels'].append(date.strftime('%a'))
        
        # This would come from your actual attendance records
        # For now using dummy data
        attendance_data['present'].append(12 - i % 3)  # Dummy data
        attendance_data['absent'].append(i % 3)  # Dummy data
    
    return jsonify(attendance_data)