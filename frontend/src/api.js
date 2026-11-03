const API_BASE_URL = 'http://127.0.0.1:5000'

export async function getCandidateMatches() {
  const response = await fetch(`${API_BASE_URL}/api/candidates/matches`)

  if (!response.ok) {
    throw new Error(`Failed to load candidates (${response.status})`)
  }

  const data = await response.json()

  if (!Array.isArray(data.candidates)) {
    throw new Error('The API response does not contain a candidates array')
  }

  return data
}

export async function updateCandidateDecision({
  candidate_email,
  job_title,
  recruiter_decision,
}) {
  const response = await fetch(`${API_BASE_URL}/api/candidates/decision`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      candidate_email,
      job_title,
      recruiter_decision,
    }),
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      data.message || `Failed to save decision (${response.status})`
    )
  }

  return data
}

export async function getInterviews() {
  const response = await fetch(`${API_BASE_URL}/api/interviews`)
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      data.message || `Failed to load interviews (${response.status})`
    )
  }

  return data.interviews || []
}

export async function createInterview(interview) {
  const response = await fetch(`${API_BASE_URL}/api/interviews`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(interview),
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      data.message || `Failed to save interview (${response.status})`
    )
  }

  return data.interview
}

export async function updateInterviewStatus(id, status) {
  const response = await fetch(`${API_BASE_URL}/api/interviews/status`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ id, status }),
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      data.message || `Failed to update interview status (${response.status})`
    )
  }

  return data
}

export async function editInterview(id, updates) {
  const response = await fetch(
    `${API_BASE_URL}/api/interviews/${encodeURIComponent(id)}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    }
  )

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      data.message || `Failed to edit interview (${response.status})`
    )
  }

  return data
}

// TEST MODE ONLY.
// This records an email draft in MongoDB.
// It does not send an actual email.
export async function saveTestEmailLog(emailDraft) {
  const response = await fetch(`${API_BASE_URL}/api/email/test-log`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(emailDraft),
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      data.message || `Failed to save test email (${response.status})`
    )
  }

  return data
}
export async function getCandidateInsights({ candidate_email, job_title }) {
  const response = await fetch(`${API_BASE_URL}/api/ai/candidate-insights`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ candidate_email, job_title }),
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      data.message || `Failed to get AI insights (${response.status})`
    )
  }

  return data.insights
}
export async function importResumes() {
  const response = await fetch(`${API_BASE_URL}/api/resumes/import`, {
    method: 'POST',
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      data.message || `Failed to import resumes (${response.status})`
    )
  }

  return data
}
export async function uploadResumes(files) {
  const formData = new FormData()
  files.forEach((file) => formData.append('resumes', file))

  const response = await fetch(`${API_BASE_URL}/api/resumes/upload`, {
    method: 'POST',
    body: formData,
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      data.message ||
        (response.status === 413
          ? 'Files are too large. Upload up to 25 MB at a time.'
          : `Upload failed (${response.status})`)
    )
  }

  return data
}
export async function getJobs() {
  const response = await fetch(`${API_BASE_URL}/api/jobs`)
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      data.message || `Failed to load job positions (${response.status})`
    )
  }

  return data.jobs || []
}

export async function createJob({ job_title, required_skills }) {
  const response = await fetch(`${API_BASE_URL}/api/jobs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ job_title, required_skills }),
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      data.message || `Failed to add position (${response.status})`
    )
  }

  return data
}