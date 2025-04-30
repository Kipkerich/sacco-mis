// Handles loan schedule generation and PDF download for Add Loan Modal
function getLoanParams() {
    return {
        amount: parseFloat(document.getElementById('amount').value) || 0,
        plan_id: document.getElementById('loan_plan').value,
        due_date: document.getElementById('due_date').value,
        ref_number: document.getElementById('ref_number').value
    };
}

document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generate-schedule-btn');
    const scheduleContainer = document.getElementById('loan-schedule-table-container');
    const downloadBtn = document.getElementById('download-schedule-pdf');

    if (generateBtn) {
        generateBtn.addEventListener('click', function() {
            const params = getLoanParams();
            if (!params.amount || !params.plan_id) {
                scheduleContainer.innerHTML = '<span class="text-danger">Please enter amount and select a loan plan.</span>';
                downloadBtn.style.display = 'none';
                return;
            }
            scheduleContainer.innerHTML = 'Generating...';
            fetch(`/loan-schedule/?amount=${params.amount}&plan_id=${params.plan_id}&due_date=${params.due_date}&ref_number=${params.ref_number}`)
                .then(res => res.text())
                .then(html => {
                    scheduleContainer.innerHTML = html;
                    downloadBtn.style.display = 'inline-block';
                    downloadBtn.href = `/loan-schedule-pdf/?amount=${params.amount}&plan_id=${params.plan_id}&due_date=${params.due_date}&ref_number=${params.ref_number}`;
                })
                .catch(() => {
                    scheduleContainer.innerHTML = '<span class="text-danger">Failed to generate schedule.</span>';
                    downloadBtn.style.display = 'none';
                });
        });
    }
});
