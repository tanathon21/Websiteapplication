// Add this as a separate JS file or include it in your script block

// Show leave balance chart
function showLeaveBalanceChart() {
    fetch('/get_leave_balance')
      .then(response => response.json())
      .then(data => {
        const ctx = document.getElementById('leaveBalanceChart').getContext('2d');
        
        new Chart(ctx, {
          type: 'bar',
          data: {
            labels: ['ลาป่วย', 'ลาพักร้อน', 'ลากิจ'],
            datasets: [
              {
                label: 'ใช้ไปแล้ว',
                data: [
                  data.sick_leave.used,
                  data.vacation_leave.used,
                  data.personal_leave.used
                ],
                backgroundColor: '#f39c12'
              },
              {
                label: 'คงเหลือ',
                data: [
                  data.sick_leave.remaining,
                  data.vacation_leave.remaining,
                  data.personal_leave.remaining
                ],
                backgroundColor: '#2ecc71'
              }
            ]
          },
          options: {
            plugins: {
              title: {
                display: true,
                text: 'วันลาคงเหลือประจำปี'
              },
            },
            responsive: true,
            scales: {
              x: {
                stacked: true,
              },
              y: {
                stacked: true,
                beginAtZero: true
              }
            }
          }
        });
        
        // Update text displays
        document.getElementById('sickLeaveRemaining').textContent = data.sick_leave.remaining;
        document.getElementById('sickLeaveTotal').textContent = data.sick_leave.total;
        document.getElementById('vacationLeaveRemaining').textContent = data.vacation_leave.remaining;
        document.getElementById('vacationLeaveTotal').textContent = data.vacation_leave.total;
        document.getElementById('personalLeaveRemaining').textContent = data.personal_leave.remaining;
        document.getElementById('personalLeaveTotal').textContent = data.personal_leave.total;
      })
      .catch(error => {
        console.error('Error fetching leave balance:', error);
        document.getElementById('leaveBalanceChartContainer').innerHTML = '<div class="alert alert-danger">ไม่สามารถโหลดข้อมูลวันลาได้</div>';
      });
  }
  
  // Load announcements with filtering
  function loadAnnouncements(page = 1, category = 'All') {
    const container = document.getElementById('announcementsList');
    container.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
    
    fetch(`/get_announcements?page=${page}&category=${category}`)
      .then(response => response.json())
      .then(data => {
        if (data.items.length === 0) {
          container.innerHTML = '<div class="text-center text-muted p-4">ยังไม่มีข่าวสาร</div>';
          return;
        }
        
        // Clear container
        container.innerHTML = '';
        
        // Add announcements
        data.items.forEach(announcement => {
          const announcementEl = document.createElement('div');
          announcementEl.className = 'list-group-item news-item px-3';
          announcementEl.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
              <span class="news-category category-${announcement.category.toLowerCase()}">${announcement.category}</span>
              <small class="text-muted">${formatDate(announcement.created_at)}</small>
            </div>
            <h6 class="mb-1 thai-font">${announcement.title}</h6>
            <p class="mb-1 small">${announcement.content.length > 100 ? announcement.content.substring(0, 100) + '...' : announcement.content}</p>
            <div class="d-flex justify-content-between align-items-center mt-2">
              <button class="btn btn-sm btn-link px-0" onclick="showAnnouncementDetail(${announcement.id})">อ่านเพิ่มเติม</button>
              <div>
                <button class="btn btn-sm btn-outline-primary border-0"><i class="far fa-thumbs-up"></i> ถูกใจ</button>
                <button class="btn btn-sm btn-outline-secondary border-0"><i class="far fa-comment"></i> แสดงความคิดเห็น</button>
              </div>
            </div>
          `;
          container.appendChild(announcementEl);
        });
        
        // Add pagination
        if (data.pages > 1) {
          const paginationEl = document.createElement('div');
          paginationEl.className = 'mt-3 d-flex justify-content-center';
          paginationEl.innerHTML = `
            <nav aria-label="Page navigation">
              <ul class="pagination">
                <li class="page-item ${data.current_page === 1 ? 'disabled' : ''}">
                  <button class="page-link" onclick="loadAnnouncements(${data.current_page - 1}, '${category}')">&laquo;</button>
                </li>
          `;
          
          for (let i = 1; i <= data.pages; i++) {
            paginationEl.querySelector('ul').innerHTML += `
              <li class="page-item ${i === data.current_page ? 'active' : ''}">
                <button class="page-link" onclick="loadAnnouncements(${i}, '${category}')">${i}</button>
              </li>
            `;
          }
          
          paginationEl.querySelector('ul').innerHTML += `
                <li class="page-item ${data.current_page === data.pages ? 'disabled' : ''}">
                  <button class="page-link" onclick="loadAnnouncements(${data.current_page + 1}, '${category}')">&raquo;</button>
                </li>
              </ul>
            </nav>
          `;
          
          container.appendChild(paginationEl);
        }
      })
      .catch(error => {
        console.error('Error fetching announcements:', error);
        container.innerHTML = '<div class="alert alert-danger">ไม่สามารถโหลดข่าวสารได้</div>';
      });
  }
  
  // Show announcement detail in modal
  function showAnnouncementDetail(id) {
    // In a real application, this would fetch the full announcement from the server
    // For this example, we'll assume we have the complete announcement data from the previous fetch
    
    // Create and show the modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'announcementDetailModal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-hidden', 'true');
    
    modal.innerHTML = `
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title thai-font"><i class="fas fa-bullhorn me-2"></i> รายละเอียดประกาศ</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" id="announcementDetailContent">
            <div class="text-center">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">ปิด</button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show the modal
    const announcementModal = new bootstrap.Modal(document.getElementById('announcementDetailModal'));
    announcementModal.show();
    
    // Dummy data - in a real app, fetch this from the server
    setTimeout(() => {
      document.getElementById('announcementDetailContent').innerHTML = `
        <div class="mb-4">
          <span class="news-category category-important mb-2 d-inline-block">สำคัญ</span>
          <h4 class="thai-font">ประกาศเรื่องวันหยุดประจำปี 2567</h4>
          <div class="d-flex justify-content-between text-muted mb-3">
            <small>โดย: ฝ่ายบุคคล</small>
            <small>วันที่: 24 เม.ย. 2568</small>
          </div>
          <div class="announcement-content thai-font">
            <p>เรียนพนักงานทุกท่าน</p>
            <p>บริษัทฯ ขอประกาศวันหยุดประจำปี 2567 เพิ่มเติมดังนี้:</p>
            <ul>
              <li>วันที่ 1 พฤษภาคม - วันแรงงานแห่งชาติ</li>
              <li>วันที่ 13 พฤษภาคม - ชดเชยวันสงกรานต์</li>
              <li>วันที่ 3 มิถุนายน - วันเฉลิมพระชนมพรรษา สมเด็จพระนางเจ้าฯ พระบรมราชินี</li>
              <li>วันที่ 28 กรกฎาคม - วันเฉลิมพระชนมพรรษา พระบาทสมเด็จพระเจ้าอยู่หัว</li>
            </ul>
            <p>หมายเหตุ: บริษัทจะปิดทำการในวันหยุดดังกล่าว พนักงานที่มีความจำเป็นต้องทำงานในวันหยุดกรุณาติดต่อผู้จัดการฝ่ายของท่านล่วงหน้า</p>
            <p>จึงประกาศมาเพื่อทราบโดยทั่วกัน</p>
            <p>ฝ่ายทรัพยากรบุคคล</p>
          </div>
        </div>
        <div class="border-top pt-3">
          <h6 class="thai-font mb-3">แสดงความคิดเห็น</h6>
          <div class="mb-3">
            <textarea class="form-control" rows="3" placeholder="แสดงความคิดเห็นของคุณที่นี่..."></textarea>
          </div>
          <button class="btn btn-primary">ส่งความคิดเห็น</button>
        </div>
      `;
    }, 500);
    
    // Clean up when the modal is hidden
    document.getElementById('announcementDetailModal').addEventListener('hidden.bs.modal', function () {
      document.body.removeChild(modal);
    });
  }
  
  // Initialize everything when the page loads
  document.addEventListener('DOMContentLoaded', function() {
    // Initialize leave balance chart if the element exists
    if (document.getElementById('leaveBalanceChart')) {
      showLeaveBalanceChart();
    }
    
    // Initialize announcements filter
    const categoryFilter = document.getElementById('announcementCategoryFilter');
    if (categoryFilter) {
      categoryFilter.addEventListener('change', function() {
        loadAnnouncements(1, this.value);
      });
      
      // Initial load
      loadAnnouncements();
    }
    
    // Initialize date validation for leave requests
    const startDateField = document.getElementById('startDate');
    const endDateField = document.getElementById('endDate');
    
    if (startDateField && endDateField) {
      startDateField.addEventListener('change', function() {
        endDateField.min = this.value;
        if (endDateField.value && new Date(endDateField.value) < new Date(this.value)) {
          endDateField.value = this.value;
        }
      });
      
      // Set minimum date to today
      const today = new Date().toISOString().split('T')[0];
      startDateField.min = today;
      endDateField.min = today;
    }
  });
  
  // Helper function to format dates
  function formatDate(dateString) {
    const options = { day: 'numeric', month: 'short', year: 'numeric' };
    return new Date(dateString).toLocaleDateString('th-TH', options);
  }