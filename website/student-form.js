// Student Information Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const studentForm = document.getElementById('studentForm');
    const nextSteps = document.getElementById('nextSteps');
    
    if (studentForm) {
        studentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(studentForm);
            const studentData = Object.fromEntries(formData);
            
            // Basic validation
            if (!validateForm(studentData)) {
                return;
            }
            
            // Send data to server
            sendDataToServer(studentData);
        });
    }
});

function sendDataToServer(data) {
    // Build URL with query parameters
    const baseUrl = 'https://zenmanenergy.pythonanywhere.com/submit';
    const params = new URLSearchParams();
    
    // Add all form fields as URL parameters
    Object.keys(data).forEach(key => {
        if (data[key]) { // Only add non-empty values
            params.append(key, data[key]);
        }
    });
    
    const fullUrl = `${baseUrl}?${params.toString()}`;
    
    // Show loading state
    const submitButton = document.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Submitting...';
    submitButton.disabled = true;
    
    // Send GET request
    fetch(fullUrl)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error(`Server responded with status: ${response.status}`);
        })
        .then(data => {
            console.log('Success:', data);
            
            if (data.status === 'success') {
                // Store data locally as backup
                localStorage.setItem('honkingNarwhalsStudentData', JSON.stringify(data));
                
                // Set cookie to indicate student info is completed
                setCookie('studentInfoCompleted', 'true', 30); // Expires in 30 days
                
                // Redirect back to join page to show completion
                window.location.href = 'join.html';
            } else {
                throw new Error(data.message || 'Unknown error occurred');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error submitting your information. Please try again or contact us directly.');
            
            // Reset button
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        });
}

function validateForm(data) {
    // Check required fields
    const requiredFields = [
        'studentFirstName',
        'studentLastName', 
        'studentEmail',
        'studentAge',
        'studentSchool',
        'parent1FirstName',
        'parent1LastName',
        'parent1Email',
        'parent1Phone'
    ];
    
    for (let field of requiredFields) {
        if (!data[field] || data[field].trim() === '') {
            alert(`Please fill in the required field: ${getFieldLabel(field)}`);
            document.getElementById(field).focus();
            return false;
        }
    }
    
    // Validate email formats
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.studentEmail)) {
        alert('Please enter a valid student email address');
        document.getElementById('studentEmail').focus();
        return false;
    }
    
    if (!emailRegex.test(data.parent1Email)) {
        alert('Please enter a valid parent/guardian email address');
        document.getElementById('parent1Email').focus();
        return false;
    }
    
    // Validate age
    const age = parseInt(data.studentAge);
    if (age < 13 || age > 19) {
        alert('Student age must be between 13 and 19');
        document.getElementById('studentAge').focus();
        return false;
    }
    
    return true;
}

function getFieldLabel(fieldName) {
    const labels = {
        'studentFirstName': 'Student First Name',
        'studentLastName': 'Student Last Name',
        'studentEmail': 'Student Email',
        'studentAge': 'Student Age',
        'studentSchool': 'Student School',
        'parent1FirstName': 'Parent/Guardian 1 First Name',
        'parent1LastName': 'Parent/Guardian 1 Last Name',
        'parent1Email': 'Parent/Guardian 1 Email',
        'parent1Phone': 'Parent/Guardian 1 Phone'
    };
    
    return labels[fieldName] || fieldName;
}

// Format phone number inputs
document.addEventListener('DOMContentLoaded', function() {
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 6) {
                value = value.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
            } else if (value.length >= 3) {
                value = value.replace(/(\d{3})(\d{0,3})/, '($1) $2');
            }
            e.target.value = value;
        });
    });
});

// Cookie helper functions
function setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
}

function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}