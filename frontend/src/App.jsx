
import { useCallback, useEffect, useState } from 'react'
import './App.css'
import './theme.css'
import {
  getCandidateMatches,
  updateCandidateDecision,
  getInterviews,
  createInterview,
  updateInterviewStatus,
  editInterview,
  saveTestEmailLog,
  getCandidateInsights,
  importResumes,
  uploadResumes,
  getJobs,
  createJob,
} from './api'

const ICONS = {
  dashboard: <><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></>,
  candidates: <><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6" /><path d="M16 4.5a3.5 3.5 0 0 1 0 7M21.5 20c0-2.6-1.5-4.5-3.5-5.4" /></>,
  matching: <><circle cx="11" cy="11" r="7" /><path d="m20.5 20.5-4.5-4.5" /></>,
  calendar: <><rect x="3" y="5" width="18" height="16" rx="2.5" /><path d="M8 3v4M16 3v4M3 10h18" /></>,
  training: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z" /><path d="M4 19V5.5" /></>,
  reports: <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />,
  check: <path d="m5 12.5 4.5 4.5L19 7.5" />,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>,
  moon: <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />,
    upload: <><path d="M12 16V4M7 9l5-5 5 5" /><path d="M4 20h16" /></>,
}

function Icon({ name, size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {ICONS[name]}
    </svg>
  )
}

const statusTabs = ['All', 'Scheduled', 'Completed', 'Cancelled']


const now = new Date()
const todayKey = [
  now.getFullYear(),
  String(now.getMonth() + 1).padStart(2, '0'),
  String(now.getDate()).padStart(2, '0'),
].join('-')

const formatInterviewDate = (dateString) => {
  const date = new Date(`${dateString}T00:00:00`)
  if (Number.isNaN(date.getTime())) return { day: '--', month: '', weekday: 'Date not set' }
  return {
    day: date.getDate(),
    month: date.toLocaleDateString('en-US', { month: 'short' }),
    weekday: date.toLocaleDateString('en-US', { weekday: 'long' }),
  }
}

const formatInterviewTime = (timeString) => {
  if (!timeString) return 'Time not set'
  const [hours, minutes] = timeString.split(':').map(Number)
  if (Number.isNaN(hours)) return timeString
  return `${((hours + 11) % 12) + 1}:${String(minutes || 0).padStart(2, '0')} ${hours >= 12 ? 'PM' : 'AM'}`
}

const keepLatestPerCandidate = (list) => {
  const latest = new Map()

  list.forEach((interview) => {
    const key = (interview.candidate_email || '').trim().toLowerCase()
    const stamp = `${interview.date || ''} ${interview.time || ''} ${interview.id || ''}`
    const current = latest.get(key)

    if (!current || stamp > current.stamp) {
      latest.set(key, { interview, stamp })
    }
  })

  return [...latest.values()].map((entry) => entry.interview)
}

const summarizeImport = (result) => {
  const added = result.added?.length || 0
  const failed = result.failed || []
  if (!added && !failed.length) return ''

  const parts = []
  if (added) parts.push(`${added} new resume${added === 1 ? '' : 's'} imported.`)
  if (failed.length) parts.push(`Could not read: ${failed.map((item) => item.file).join(', ')}.`)
  return parts.join(' ')
}

function ScoreRing({ value }) {
  const score = Math.max(0, Math.min(100, Number(value) || 0))
  const radius = 18
  const circumference = 2 * Math.PI * radius
  const tone = score >= 80 ? 'high' : score >= 50 ? 'mid' : 'low'

  return (
    <div className={`score-ring ${tone}`} title={`${score}% skill match`}>
      <svg width="48" height="48" viewBox="0 0 48 48" aria-hidden="true">
        <circle className="ring-track" cx="24" cy="24" r={radius} />
        <circle
          className="ring-fill"
          cx="24"
          cy="24"
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - score / 100)}
        />
      </svg>
      <span>{Math.round(score)}</span>
    </div>
  )
}

function CountUp({ value }) {
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce) {
      setDisplay(value)
      return undefined
    }

    let frame
    const start = performance.now()
    const tick = (time) => {
      const progress = Math.min((time - start) / 700, 1)
      setDisplay(Math.round(value * (1 - Math.pow(1 - progress, 3))))
      if (progress < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [value])

  return <>{display}</>
}

function Toggle({ checked, onChange, label }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      className={`switch ${checked ? 'on' : ''}`}
      onClick={() => onChange(!checked)}
    >
      <span className="switch-track">
        <span className="switch-thumb" />
      </span>
      <span className="switch-label">{label}</span>
    </button>
  )
}
const KNOWN_SKILLS = [
  'Python', 'Java', 'JavaScript', 'Flask', 'Django', 'SQL', 'MySQL',
  'MongoDB', 'React', 'Node.js', 'HTML', 'CSS', 'Bootstrap',
  'Machine Learning', 'Git', 'REST APIs', 'PyMuPDF', 'Postman', 'C++', 'C',
]

function App() {
  const [importNotice, setImportNotice] = useState('')
  const [upcomingOnly, setUpcomingOnly] = useState(true)
  const [jobs, setJobs] = useState([])
const [selectedJobTitle, setSelectedJobTitle] = useState('')
const [showJobForm, setShowJobForm] = useState(false)
const [newJobTitle, setNewJobTitle] = useState('')
const [newJobSkills, setNewJobSkills] = useState([])
const [skillInput, setSkillInput] = useState('')
const [jobSaving, setJobSaving] = useState(false)
const [jobError, setJobError] = useState('')
  const [paletteOpen, setPaletteOpen] = useState(false)
const [paletteQuery, setPaletteQuery] = useState('')
const [paletteIndex, setPaletteIndex] = useState(0)
  const [uploading, setUploading] = useState(false)
const [dragActive, setDragActive] = useState(false)
const [uploadResult, setUploadResult] = useState(null)
  const [topJobTab, setTopJobTab] = useState('')
  const [aiCandidate, setAiCandidate] = useState(null)
const [aiInsights, setAiInsights] = useState(null)
const [aiLoading, setAiLoading] = useState(false)
const [aiError, setAiError] = useState('')
  const [showInterviewForm, setShowInterviewForm] = useState(false)
  const [editingInterview, setEditingInterview] = useState(null)
const [selectedCandidate, setSelectedCandidate] = useState(null)
const [interviewDate, setInterviewDate] = useState('')
const [interviewTime, setInterviewTime] = useState('')
const [interviewDuration, setInterviewDuration] = useState('30')
const [interviewMode, setInterviewMode] = useState('Online')
const [interviewNotes, setInterviewNotes] = useState('')
const [scheduledInterviews, setScheduledInterviews] = useState([])
const [interviewSearch, setInterviewSearch] = useState('')
const [interviewStatusFilter, setInterviewStatusFilter] = useState('All')
  const [candidates, setCandidates] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
const [jobFilter, setJobFilter] = useState('all')
const [emailPreviewInterview, setEmailPreviewInterview] = useState(null);
const [emailComposer, setEmailComposer] = useState(null);
const [savingTestEmail, setSavingTestEmail] = useState(false);
const [testEmailMessage, setTestEmailMessage] = useState('');
const [darkMode, setDarkMode] = useState(() => {
  try {
    return localStorage.getItem('recruitai-theme') === 'dark'
  } catch {
    return false
  }
})
const [shortlistedOnly, setShortlistedOnly] = useState(false)
const [compactRows, setCompactRows] = useState(false)
const [calendarMonth, setCalendarMonth] = useState(new Date());
const [selectedCalendarDate, setSelectedCalendarDate] = useState(
  `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}-${String(new Date().getDate()).padStart(2, '0')}`
);
const [currentPage, setCurrentPage] = useState('dashboard');
useEffect(() => {
  document.documentElement.dataset.theme = darkMode ? 'dark' : 'light'
  try {
    localStorage.setItem('recruitai-theme', darkMode ? 'dark' : 'light')
  } catch {
    /* storage unavailable, the theme still works for this session */
  }
}, [darkMode])

useEffect(() => {
  const onKey = (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault()
      setPaletteOpen((open) => !open)
      setPaletteQuery('')
      setPaletteIndex(0)
    }
    if (event.key === 'Escape') setPaletteOpen(false)
  }

  window.addEventListener('keydown', onKey)
  return () => window.removeEventListener('keydown', onKey)
}, [])

  const openEmailComposer = (candidate) => {
    const interview = scheduledInterviews.find(
      (item) =>
        (item.candidate_email || '').toLowerCase() ===
          (candidate.candidate_email || '').toLowerCase() &&
        item.job_title === candidate.job_title &&
        (item.status || 'Scheduled') !== 'Cancelled'
    )

    const candidateName = candidate.candidate_name || ''
    const jobTitle = candidate.job_title || ''
    const date = interview?.date || ''
    const time = interview?.time || ''
    const duration = interview?.duration || 30
    const mode = interview?.mode || 'Online'

    setTestEmailMessage('')
    setEmailComposer({
      candidate_name: candidateName,
      candidate_email: candidate.candidate_email || 'candidate@example.com',
      job_title: jobTitle,
      subject: `Interview Invitation - ${jobTitle || 'Job Position'}`,
      interview_date: date,
      interview_time: time,
      duration: String(duration),
      mode,
      body: `Dear ${candidateName || 'Candidate'},\n\nWe are pleased to invite you for an interview for the ${jobTitle || 'position'} role.\n\nInterview date: ${date || '[Add interview date]'}\nInterview time: ${time || '[Add interview time]'}\nDuration: ${duration} minutes\nMode: ${mode}\n\nPlease contact the recruitment team if you have any questions.\n\nBest regards,\nRecruitAI Recruitment Team`,
    })
  }

  const updateEmailDraftField = (field, value) => {
    setEmailComposer((previous) => {
      if (!previous) return previous
      const next = { ...previous, [field]: value }
      if (field === 'candidate_name' || field === 'job_title') {
        const name = field === 'candidate_name' ? value : next.candidate_name
        const job = field === 'job_title' ? value : next.job_title
        next.subject = `Interview Invitation - ${job || 'Job Position'}`
        next.body = next.body
          .replace(/^Dear .*?,/m, `Dear ${name || 'Candidate'},`)
          .replace(/for the .*? role\./, `for the ${job || 'position'} role.`)
      }
      if (field === 'interview_date') {
        next.body = next.body.replace(/^Interview date: .*$/m, `Interview date: ${value || '[Add interview date]'}`)
      }
      if (field === 'interview_time') {
        next.body = next.body.replace(/^Interview time: .*$/m, `Interview time: ${value || '[Add interview time]'}`)
      }
      if (field === 'duration') {
        next.body = next.body.replace(/^Duration: .*$/m, `Duration: ${value} minutes`)
      }
      if (field === 'mode') {
        next.body = next.body.replace(/^Mode: .*$/m, `Mode: ${value}`)
      }
      return next
    })
  }

  const handleSaveTestEmail = async (event) => {
    event.preventDefault()
    if (!emailComposer) return

    setSavingTestEmail(true)
    setTestEmailMessage('')
    try {
      const result = await saveTestEmailLog({
        ...emailComposer,
        duration: Number(emailComposer.duration || 30),
        test_mode: true,
      })
      setTestEmailMessage(result.message || 'Test email recorded. No email was delivered.')
    } catch (error) {
      setTestEmailMessage(error.message || 'Could not save the test email record.')
    } finally {
      setSavingTestEmail(false)
    }
  }

  const loadCandidates = useCallback(async () => {
    try {
      setError('')
      setRefreshing(true)
      const data = await getCandidateMatches()
      setCandidates(data.candidates || [])
    } catch {
      setError('Could not load candidates. Please check that Flask is running.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  const loadJobs = useCallback(async () => {
  try {
    setJobs(await getJobs())
  } catch (error) {
    console.error('Could not load job positions:', error)
  }
}, [])


const handleDecisionChange = async (candidate, newDecision) => {
  try {
    await updateCandidateDecision({
      candidate_email: candidate.candidate_email,
      job_title: candidate.job_title,
      recruiter_decision: newDecision,
    })

    await loadCandidates()
  } catch (error) {
    window.alert(
      error.message || 'Could not save the candidate decision.'
    )

    await loadCandidates()
  }
}
const addJobSkill = (value) => {
  const skill = value.trim().replace(/,$/, '')
  if (!skill) return
  setNewJobSkills((previous) =>
    previous.some((item) => item.toLowerCase() === skill.toLowerCase())
      ? previous
      : [...previous, skill]
  )
  setSkillInput('')
}

const closeJobForm = () => {
  setShowJobForm(false)
  setNewJobTitle('')
  setNewJobSkills([])
  setSkillInput('')
  setJobError('')
}

const handleCreateJob = async (event) => {
  event.preventDefault()

  const skills = [...newJobSkills]
  const pending = skillInput.trim()
  if (pending && !skills.some((item) => item.toLowerCase() === pending.toLowerCase())) {
    skills.push(pending)
  }

  setJobSaving(true)
  setJobError('')

  try {
    await createJob({ job_title: newJobTitle.trim(), required_skills: skills })
    await Promise.all([loadJobs(), loadCandidates()])
    setSelectedJobTitle(newJobTitle.trim())
    closeJobForm()
  } catch (error) {
    setJobError(error.message || 'Could not add the position.')
  } finally {
    setJobSaving(false)
  }
}

const syncResumes = async () => {
  setRefreshing(true)
  try {
    const result = await importResumes()
    setImportNotice(summarizeImport(result))
  } catch (error) {
    setImportNotice(error.message || 'Could not import resumes.')
  }
  await loadCandidates()
}
const handleResumeFiles = async (fileList) => {
  const files = Array.from(fileList || [])
  if (!files.length) return

  setUploading(true)
  setUploadResult(null)

  try {
    const result = await uploadResumes(files)
    setUploadResult(result)
    await loadCandidates()
  } catch (error) {
    setUploadResult({ error: error.message || 'Upload failed.' })
  } finally {
    setUploading(false)
  }
}

const openAiInsights = async (candidate) => {
  setAiCandidate(candidate)
  setAiInsights(null)
  setAiError('')
  setAiLoading(true)

  try {
    const insights = await getCandidateInsights({
      candidate_email: candidate.candidate_email,
      job_title: candidate.job_title,
    })
    setAiInsights(insights)
  } catch (error) {
    setAiError(error.message || 'Could not generate AI insights.')
  } finally {
    setAiLoading(false)
  }
}

const closeAiInsights = () => {
  setAiCandidate(null)
  setAiInsights(null)
  setAiError('')
}


const handleInterviewStatusChange = async (interview, newStatus) => {
  if (
    newStatus === 'Cancelled' &&
    !window.confirm(
      `Are you sure you want to cancel the interview with ${interview.candidate_name}?`
    )
  ) {
    return
  }

  try {
    await updateInterviewStatus(interview.id, newStatus)

    setScheduledInterviews((previous) =>
      previous.map((item) =>
        item.id === interview.id
          ? { ...item, status: newStatus }
          : item
      )
    )
  } catch (error) {
    window.alert(error.message || 'Could not update interview status.')
  }
}




useEffect(() => {
  loadCandidates()
  loadJobs()

  importResumes()
    .then((result) => {
      setImportNotice(summarizeImport(result))
      if (result.added?.length) loadCandidates()
    })
    .catch((error) => {
      console.error('Resume import skipped:', error)
    })

  getInterviews()
    .then((interviews) => {
      setScheduledInterviews(keepLatestPerCandidate(interviews))
    })
    .catch((error) => {
      console.error('Could not load saved interviews:', error)
    })
}, [loadCandidates, loadJobs])



  const jobTitles = [
    ...new Set(
      candidates.map((candidate) => candidate.job_title).filter(Boolean)
    ),
  ]

  const topJob = jobTitles.includes(topJobTab) ? topJobTab : (jobTitles[0] || '')

const topMatches = candidates
  .filter((candidate) => candidate.job_title === topJob)
  .sort(
    (a, b) =>
      Number(b.skill_match_score_percent ?? 0) -
      Number(a.skill_match_score_percent ?? 0)
  )
  .slice(0, 3)

 const filteredCandidates = candidates.filter((candidate) => {
  const query = searchTerm.toLowerCase().trim()

  const matchesSearch =
    candidate.candidate_name?.toLowerCase().includes(query) ||
    candidate.candidate_email?.toLowerCase().includes(query)

  const matchesJob =
    jobFilter === 'all' || candidate.job_title === jobFilter

  const matchesDecision =
    !shortlistedOnly || candidate.recruiter_decision === 'Shortlisted'

  return matchesSearch && matchesJob && matchesDecision
})

const visibleInterviews = upcomingOnly
  ? scheduledInterviews.filter(
      (interview) => interview.date && interview.date >= todayKey
    )
  : scheduledInterviews

const filteredInterviews = visibleInterviews
  .filter((interview) => {
    const search = interviewSearch.trim().toLowerCase()

    const matchesSearch =
      (interview.candidate_name || '').toLowerCase().includes(search) ||
      (interview.candidate_email || '').toLowerCase().includes(search) ||
      (interview.job_title || '').toLowerCase().includes(search)

    const matchesStatus =
      interviewStatusFilter === 'All' ||
      (interview.status || 'Scheduled') === interviewStatusFilter

    return matchesSearch && matchesStatus
  })
  .sort((a, b) =>
    `${a.date || ''} ${a.time || ''}`.localeCompare(
      `${b.date || ''} ${b.time || ''}`
    )
  )

const scheduledCount = scheduledInterviews.filter(
  (interview) => (interview.status || 'Scheduled') === 'Scheduled'
).length

const completedCount = scheduledInterviews.filter(
  (interview) => interview.status === 'Completed'
).length

const cancelledCount = scheduledInterviews.filter(
  (interview) => interview.status === 'Cancelled'
).length
const statusCount = (tab) =>
  tab === 'All'
    ? visibleInterviews.length
    : visibleInterviews.filter(
        (interview) => (interview.status || 'Scheduled') === tab
      ).length

const calendarYear = calendarMonth.getFullYear();
const calendarMonthIndex = calendarMonth.getMonth();

const daysInMonth = new Date(
  calendarYear,
  calendarMonthIndex + 1,
  0
).getDate();

const firstDayOfMonth = new Date(
  calendarYear,
  calendarMonthIndex,
  1
).getDay();

const calendarCells = [
  ...Array(firstDayOfMonth).fill(null),
  ...Array.from({ length: daysInMonth }, (_, index) => index + 1),
];

const calendarMonthLabel = calendarMonth.toLocaleDateString('en-US', {
  month: 'long',
  year: 'numeric',
});
  const shortlisted = candidates.filter(
    (candidate) => candidate.recruiter_decision === 'Shortlisted'
  ).length

  const interviews = candidates.filter(
    (candidate) => candidate.recruitment_status === 'Interview Scheduled'
  ).length

  const hour = new Date().getHours()
const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
const todayLabel = new Date().toLocaleDateString('en-IN', {
  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
})
const awaitingDecision = candidates.filter((candidate) =>
  ['Not Decided', 'Under Review'].includes(candidate.recruiter_decision || 'Not Decided')
).length

const paletteCommands = [
  { id: 'go-dashboard', label: 'Go to Dashboard', hint: 'Navigate', run: () => setCurrentPage('dashboard') },
  { id: 'go-calendar', label: 'Go to Interview Calendar', hint: 'Navigate', run: () => setCurrentPage('calendar') },
  { id: 'go-reports', label: 'Go to Reports', hint: 'Navigate', run: () => setCurrentPage('reports') },
    { id: 'go-jobs', label: 'Go to Job Matching', hint: 'Navigate', run: () => setCurrentPage('jobs') },
  {
    id: 'toggle-theme',
    label: darkMode ? 'Switch to light mode' : 'Switch to dark mode',
    hint: 'Appearance',
    run: () => setDarkMode((value) => !value),
  },
  {
    id: 'toggle-shortlisted',
    label: shortlistedOnly ? 'Show all candidates' : 'Show shortlisted candidates only',
    hint: 'Filter',
    run: () => {
      setCurrentPage('dashboard')
      setShortlistedOnly((value) => !value)
    },
  },
  {
    id: 'refresh',
    label: 'Refresh candidates and import new resumes',
    hint: 'Action',
    run: () => {
      setCurrentPage('dashboard')
      syncResumes()
    },
  },
]

const paletteCandidates = candidates.map((candidate, index) => ({
  id: `candidate-${index}`,
  label: candidate.candidate_name || 'Unknown',
  hint: `${candidate.job_title || 'No job'} · ${Number(candidate.skill_match_score_percent ?? 0)}%`,
  search: `${candidate.candidate_name || ''} ${candidate.candidate_email || ''} ${candidate.job_title || ''}`,
  run: () => {
    setCurrentPage('dashboard')
    openAiInsights(candidate)
  },
}))

const paletteSearch = paletteQuery.trim().toLowerCase()

const paletteResults = [
  ...paletteCommands.filter(
    (item) => !paletteSearch || item.label.toLowerCase().includes(paletteSearch)
  ),
  ...(paletteSearch
    ? paletteCandidates
        .filter((item) => item.search.toLowerCase().includes(paletteSearch))
        .slice(0, 6)
    : []),
]

const runPaletteItem = (item) => {
  setPaletteOpen(false)
  if (item) item.run()
}

const jobStats = jobs.map((job) => {
  const rows = candidates
    .filter((candidate) => candidate.job_title === job.job_title)
    .sort(
      (a, b) =>
        Number(b.skill_match_score_percent ?? 0) -
        Number(a.skill_match_score_percent ?? 0)
    )

  const scores = rows.map((row) => Number(row.skill_match_score_percent ?? 0))
  const average = scores.length
    ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
    : 0

  const coverage = (job.required_skills || []).map((skill) => ({
    skill,
    count: rows.filter((row) =>
      (row.matched_skills || []).some(
        (matched) => String(matched).toLowerCase() === skill.toLowerCase()
      )
    ).length,
  }))

  return { ...job, rows, average, best: rows[0] || null, coverage }
})

const activeJob =
  jobStats.find((job) => job.job_title === selectedJobTitle) || jobStats[0] || null

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">R</div>
          <div>
            <h2>RecruitAI</h2>
            <p>Recruitment Platform</p>
          </div>
        </div>

        <p className="nav-section-title">WORKSPACE</p>

        <nav className="sidebar-nav" aria-label="Main navigation">
  {[
    { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
    { id: 'calendar', label: 'Interview Calendar', icon: 'calendar', badge: scheduledCount },
        { id: 'jobs', label: 'Job Matching', icon: 'matching' },
    { id: 'reports', label: 'Reports', icon: 'reports' },
  ].map((item) => (
    <button
      key={item.id}
      type="button"
      className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
      onClick={() => setCurrentPage(item.id)}
      aria-current={currentPage === item.id ? 'page' : undefined}
    >
      <Icon name={item.icon} />
      <span className="nav-label">{item.label}</span>
      {item.badge > 0 && <span className="nav-badge">{item.badge}</span>}
    </button>
  ))}

  <p className="nav-section-title nav-soon-title">COMING SOON</p>
    {[['Candidates', 'candidates'], ['Training', 'training']].map(([label, icon]) => (
    <div className="nav-item disabled" key={label} aria-disabled="true">
      <Icon name={icon} />
      <span className="nav-label">{label}</span>
      <span className="nav-soon">Soon</span>
    </div>
  ))}
</nav>

        <div className="sidebar-footer">
          <div className="profile-avatar">R</div>
          <div>
            <strong>Recruiter</strong>
            <span>Recruitment Team</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        {currentPage === 'calendar' && (
          <section className="table-card calendar-page-card">
            <div className="table-heading calendar-page-heading">
              <div>
                <h2>Interview Calendar</h2>
                <p>Select a date to see its interviews on the right.</p>
              </div>
              <button
                type="button"
                className="schedule-interview-button"
                onClick={() => setCurrentPage('dashboard')}
              >
                Back to Dashboard
              </button>
            </div>

            <div className="calendar-page-layout">
              <div className="interview-calendar">
                <div className="calendar-header">
                  <button
                    type="button"
                    onClick={() => {
                      const previousMonth = new Date(calendarYear, calendarMonthIndex - 1, 1)
                      setCalendarMonth(previousMonth)
                      setSelectedCalendarDate(`${previousMonth.getFullYear()}-${String(previousMonth.getMonth() + 1).padStart(2, '0')}-01`)
                    }}
                  >
                    ← Previous
                  </button>
                  <h3>{calendarMonthLabel}</h3>
                  <button
                    type="button"
                    onClick={() => {
                      const nextMonth = new Date(calendarYear, calendarMonthIndex + 1, 1)
                      setCalendarMonth(nextMonth)
                      setSelectedCalendarDate(`${nextMonth.getFullYear()}-${String(nextMonth.getMonth() + 1).padStart(2, '0')}-01`)
                    }}
                  >
                    Next →
                  </button>
                </div>

                <div className="calendar-grid">
                  {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                    <div className="calendar-weekday" key={day}>{day}</div>
                  ))}

                  {calendarCells.map((day, index) => {
                    if (day === null) {
                      return <div className="calendar-day empty" key={`empty-${index}`} />
                    }

                    const dateKey = [
                      calendarYear,
                      String(calendarMonthIndex + 1).padStart(2, '0'),
                      String(day).padStart(2, '0'),
                    ].join('-')
                    const dayInterviews = scheduledInterviews.filter((interview) => interview.date === dateKey)
                    const isSelected = selectedCalendarDate === dateKey

                    return (
                      <button
                        type="button"
                        className={`calendar-day calendar-day-button ${isSelected ? 'selected' : ''}`}
                        key={dateKey}
                        onClick={() => setSelectedCalendarDate(dateKey)}
                        aria-label={`${dateKey}${dayInterviews.length ? `, ${dayInterviews.length} interviews` : ''}`}
                        aria-pressed={isSelected}
                      >
                        <strong>{day}</strong>
                        {dayInterviews.length > 0 && (
                          <span className="calendar-event-dot" title={`${dayInterviews.length} interview(s)`}>
                            {dayInterviews.length > 1 ? dayInterviews.length : '•'}
                          </span>
                        )}
                      </button>
                    )
                  })}
                </div>

                <p className="calendar-note">
                  A dot or number marks dates with interviews. Select a date to view details.
                </p>
              </div>

              <aside className="calendar-day-details">
                <h3>
                  Interviews on {new Date(`${selectedCalendarDate}T00:00:00`).toLocaleDateString('en-US', {
                    month: 'long', day: 'numeric', year: 'numeric'
                  })}
                </h3>
                {scheduledInterviews.filter((interview) => interview.date === selectedCalendarDate).length === 0 ? (
                  <div className="empty-state calendar-empty-state">
                    <strong>No interviews on this date</strong>
                    <span>Select another date marked on the calendar.</span>
                  </div>
                ) : (
                  <div className="calendar-selected-interviews">
                    {scheduledInterviews
                      .filter((interview) => interview.date === selectedCalendarDate)
                      .sort((a, b) => (a.time || '').localeCompare(b.time || ''))
                      .map((interview) => (
                        <article
                          className="calendar-interview-card compact-interview-card"
                          key={interview.id || `${interview.date}-${interview.time}-${interview.candidate_email}`}
                        >
                          <div className="compact-interview-top">
                            <strong>{interview.time || 'Time not set'}</strong>
                            <span className={`compact-status ${(interview.status || 'Scheduled').toLowerCase()}`}>
                              {interview.status || 'Scheduled'}
                            </span>
                          </div>
                          <div className="compact-interview-info">
                            <strong>{interview.candidate_name || 'Unknown candidate'}</strong>
                            <span>{interview.job_title || 'Job not specified'}</span>
                          </div>
                        </article>
                      ))}
                  </div>
                )}
              </aside>
            </div>
          </section>
        )}

{currentPage === 'reports' && (
  <section className="reports-page">
    <div className="reports-heading">
      <div>
        <p className="page-eyebrow">WORKSPACE / ANALYTICS</p>
        <h1>Recruitment Reports</h1>
        <p>Review candidate decisions, matching performance, and interview outcomes.</p>
      </div>
      <button type="button" className="schedule-interview-button" onClick={() => setCurrentPage('dashboard')}>
        Back to Dashboard
      </button>
    </div>

    <div className="reports-stats">
      <article className="report-stat-card">
        <div className="report-stat-top"><span>Total Candidates</span><span className="report-stat-icon icon-blue">♙</span></div>
        <h2>{candidates.length}</h2>
        <p>Candidate match records</p>
      </article>
      <article className="report-stat-card">
        <div className="report-stat-top"><span>Shortlisted</span><span className="report-stat-icon icon-green">✓</span></div>
        <h2>{candidates.filter((candidate) => candidate.recruiter_decision === 'Shortlisted').length}</h2>
        <p>Marked by the recruiter</p>
      </article>
      <article className="report-stat-card">
        <div className="report-stat-top"><span>Scheduled Interviews</span><span className="report-stat-icon icon-purple">▣</span></div>
        <h2>{scheduledCount}</h2>
        <p>Interview sessions scheduled</p>
      </article>
      <article className="report-stat-card">
        <div className="report-stat-top"><span>Completed Interviews</span><span className="report-stat-icon icon-orange">✓</span></div>
        <h2>{completedCount}</h2>
        <p>Interview sessions completed</p>
      </article>
    </div>

    <div className="reports-two-column">
      <section className="table-card reports-table-card">
        <div className="table-heading">
          <div>
            <h2>Recruitment Decisions</h2>
            <p>Current recruiter decisions across candidate records.</p>
          </div>
        </div>
        {['Not Decided', 'Under Review', 'Shortlisted', 'Rejected'].map((decision) => {
          const count = candidates.filter((candidate) =>
            (candidate.recruiter_decision || 'Not Decided') === decision
          ).length
          const percent = candidates.length ? Math.round((count / candidates.length) * 100) : 0
          return (
            <div className={`report-progress-row decision-${decision.toLowerCase().replaceAll(' ', '-')}`} key={decision}>
              <div className="report-progress-label">
                <span>{decision}</span>
                <strong>{count} ({percent}%)</strong>
              </div>
              <div className="report-progress-track">
                <div className="report-progress-fill" style={{ width: `${percent}%` }} />
              </div>
            </div>
          )
        })}
      </section>

      <section className="table-card reports-table-card">
        <div className="table-heading">
          <div>
            <h2>Interview Outcomes</h2>
            <p>Breakdown of interviews by their current status.</p>
          </div>
        </div>
        {[
          { label: 'Scheduled', count: scheduledCount },
          { label: 'Completed', count: completedCount },
          { label: 'Cancelled', count: cancelledCount },
        ].map((item) => {
          const percent = scheduledInterviews.length
            ? Math.round((item.count / scheduledInterviews.length) * 100)
            : 0
          return (
            <div className={`report-progress-row outcome-${item.label.toLowerCase()}`} key={item.label}>
              <div className="report-progress-label">
                <span>{item.label}</span>
                <strong>{item.count} ({percent}%)</strong>
              </div>
              <div className="report-progress-track">
                <div className="report-progress-fill" style={{ width: `${percent}%` }} />
              </div>
            </div>
          )
        })}
      </section>
    </div>

    <section className="table-card reports-table-card reports-activity-card">
      <div className="table-heading">
        <div>
          <h2>Recruitment Activity</h2>
          <p>Candidate matching scores and current recruiter decisions.</p>
        </div>
        <span className="report-table-count">{candidates.length} records</span>
      </div>
      {candidates.length === 0 ? (
        <div className="empty-state">
          <strong>No candidate records available</strong>
          <span>Candidate activity will appear here when records are loaded.</span>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="reports-activity-table">
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Job Position</th>
                <th>Skill Match</th>
                <th>Decision</th>
                <th>Recruitment Status</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((candidate, index) => (
                <tr key={`${candidate.candidate_email}-${candidate.job_title}-${index}`}>
                  <td>
                    <div className="candidate-details">
                      <strong>{candidate.candidate_name || 'Unknown candidate'}</strong>
                      <span>{candidate.candidate_email || 'No email available'}</span>
                    </div>
                  </td>
                  <td>{candidate.job_title || 'Not specified'}</td>
                  <td><span className="match-score">{Number(candidate.skill_match_score_percent ?? 0)}%</span></td>
                  <td>
                    <span className={`report-decision-pill decision-pill-${(candidate.recruiter_decision || 'Not Decided').toLowerCase().replaceAll(' ', '-')}`}>
                      {candidate.recruiter_decision || 'Not Decided'}
                    </span>
                  </td>
                  <td>{candidate.recruitment_status || 'Not Set'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>

    <section className="table-card reports-table-card reports-upcoming-card">
      <div className="table-heading">
        <div>
          <h2>Upcoming Interviews</h2>
          <p>Next scheduled interview sessions.</p>
        </div>
        <button type="button" className="schedule-interview-button" onClick={() => setCurrentPage('calendar')}>
          Open Interview Calendar
        </button>
      </div>
      {scheduledInterviews.filter((interview) => (interview.status || 'Scheduled') === 'Scheduled').length === 0 ? (
        <div className="empty-state">
          <strong>No scheduled interviews</strong>
          <span>New scheduled interviews will appear here.</span>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="reports-activity-table">
            <thead>
              <tr><th>Candidate</th><th>Job Position</th><th>Date</th><th>Time</th><th>Mode</th></tr>
            </thead>
            <tbody>
              {[...scheduledInterviews]
                .filter((interview) => (interview.status || 'Scheduled') === 'Scheduled')
                .sort((a, b) => `${a.date || ''} ${a.time || ''}`.localeCompare(`${b.date || ''} ${b.time || ''}`))
                .slice(0, 5)
                .map((interview, index) => (
                  <tr key={interview.id || `${interview.candidate_email}-${interview.date}-${index}`}>
                    <td><div className="candidate-details"><strong>{interview.candidate_name || 'Unknown candidate'}</strong><span>{interview.candidate_email || 'No email available'}</span></div></td>
                    <td>{interview.job_title || 'Not specified'}</td>
                    <td>{interview.date || 'Not set'}</td>
                    <td>{interview.time || 'Not set'}</td>
                    <td>{interview.mode || 'Not specified'}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  </section>
)}

{currentPage === 'jobs' && (
  <section className="jobs-page">
    <div className="reports-heading">
      <div>
        <p className="page-eyebrow">WORKSPACE / MATCHING</p>
        <h1>Job Matching</h1>
        <p>See how well your candidate pool fits each open position.</p>
      </div>
      <button type="button" className="schedule-interview-button" onClick={() => setShowJobForm(true)}>
        + Add position
      </button>
    </div>

    {jobStats.length === 0 ? (
      <section className="table-card">
        <div className="empty-state">
          <strong>No job positions yet</strong>
          <span>Click Add position to create your first one.</span>
        </div>
      </section>
    ) : (
      <>
        <div className="job-grid">
          {jobStats.map((job) => (
            <button
              type="button"
              key={job.job_id || job.job_title}
              className={`job-card ${activeJob?.job_title === job.job_title ? 'active' : ''}`}
              onClick={() => setSelectedJobTitle(job.job_title)}
              aria-pressed={activeJob?.job_title === job.job_title}
            >
              <strong>{job.job_title}</strong>
              <span className="job-meta">
                {job.required_skills.length} required skills · {job.rows.length} candidates
              </span>
              <div className="job-card-stats">
                <div>
                  <em>{job.average}%</em>
                  <small>avg match</small>
                </div>
                <div>
                  <em>{job.best ? `${Math.round(Number(job.best.skill_match_score_percent ?? 0))}%` : '-'}</em>
                  <small>{job.best ? job.best.candidate_name : 'no candidates'}</small>
                </div>
              </div>
            </button>
          ))}
        </div>

        {activeJob && (
          <div className="job-detail">
            <section className="table-card">
              <div className="table-heading">
                <div>
                  <h2>Skill coverage</h2>
                  <p>
                    How many of your {activeJob.rows.length} candidates have each skill
                    {' '}{activeJob.job_title} requires.
                  </p>
                </div>
              </div>

              {activeJob.coverage.map(({ skill, count }) => {
                const percent = activeJob.rows.length
                  ? Math.round((count / activeJob.rows.length) * 100)
                  : 0
                const tone = percent >= 70 ? 'high' : percent >= 40 ? 'mid' : 'low'

                return (
                  <div className="cov-row" key={skill}>
                    <div className="cov-label">
                      <span>{skill}</span>
                      <strong>{count} of {activeJob.rows.length}</strong>
                    </div>
                    <div className="cov-track">
                      <i className={`cov-fill ${tone}`} style={{ width: `${percent}%` }} />
                    </div>
                  </div>
                )
              })}
            </section>

            <section className="table-card">
              <div className="table-heading">
                <div>
                  <h2>Ranked candidates</h2>
                  <p>Best fit first for {activeJob.job_title}.</p>
                </div>
                <span className="report-table-count">{activeJob.rows.length} candidates</span>
              </div>

              {activeJob.rows.length === 0 ? (
                <div className="empty-state">
                  <strong>No candidates yet</strong>
                  <span>Upload resumes on the dashboard to see them ranked here.</span>
                </div>
              ) : (
                <ol className="rank-list">
                  {activeJob.rows.map((candidate, index) => {
                    const decision = candidate.recruiter_decision || 'Not Decided'

                    return (
                      <li className="rank-row" key={`${candidate.candidate_email}-${index}`}>
                        <span className="rank-num">{index + 1}</span>
                        <ScoreRing value={candidate.skill_match_score_percent} />
                        <div className="candidate-details rank-who">
                          <strong>{candidate.candidate_name || 'Unknown'}</strong>
                          <span>{candidate.candidate_email || 'No email available'}</span>
                        </div>
                        <div className="skill-chips">
                          {(candidate.matched_skills || []).map((skill) => (
                            <span className="tag tag-ok" key={`ok-${skill}`}>{skill}</span>
                          ))}
                          {(candidate.missing_skills || []).map((skill) => (
                            <span className="tag tag-miss" key={`miss-${skill}`}>− {skill}</span>
                          ))}
                        </div>
                        {decision === 'Shortlisted' ? (
                          <span className="chip chip-today">✓ Shortlisted</span>
                        ) : (
                          <button
                            type="button"
                            className="row-btn"
                            onClick={() => handleDecisionChange(candidate, 'Shortlisted')}
                          >
                            Shortlist
                          </button>
                        )}
                      </li>
                    )
                  })}
                </ol>
              )}
            </section>
          </div>
        )}
      </>
    )}
  </section>
)}

{currentPage === 'dashboard' && (
  <>
        <header className="topbar">
  <div>
    <p className="page-eyebrow">WORKSPACE / OVERVIEW</p>
    <h1>Recruitment Dashboard</h1>
    <p className="page-description">Monitor candidates and track your recruitment progress.</p>
  </div>
  <div className="topbar-right">
    <button
  type="button"
  className="cmd-trigger"
  onClick={() => {
    setPaletteQuery('')
    setPaletteIndex(0)
    setPaletteOpen(true)
  }}
>
  <Icon name="matching" size={16} />
  <span>Search or jump to...</span>
  <kbd>Ctrl K</kbd>
</button>
    <button
  type="button"

  className="theme-toggle"
  onClick={() => setDarkMode(!darkMode)}
  aria-pressed={darkMode}
  aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
  title={darkMode ? 'Light mode' : 'Dark mode'}
>
  <Icon key={darkMode ? 'sun' : 'moon'} name={darkMode ? 'sun' : 'moon'} />
</button>
    <span className="date-chip"><Icon name="calendar" size={16} />{todayLabel}</span>
    <div className="topbar-profile">
      <div className="profile-avatar">R</div>
      <div>
        <strong>Recruiter</strong>
        <span>Administrator</span>
      </div>
    </div>
  </div>
</header>

<section className="welcome-card">
  <div>
    <p className="welcome-eyebrow">RECRUITMENT OVERVIEW</p>
    <h2>{greeting}, Recruiter</h2>
    <p>
      You have <strong>{scheduledCount}</strong> upcoming {scheduledCount === 1 ? 'interview' : 'interviews'} and{' '}
      <strong>{awaitingDecision}</strong> {awaitingDecision === 1 ? 'candidate' : 'candidates'} awaiting a decision.
    </p>
  </div>
  <div className="welcome-actions">
    <button type="button" className="welcome-btn" onClick={() => setCurrentPage('calendar')}>View calendar</button>
    <button type="button" className="welcome-btn ghost" onClick={() => setCurrentPage('reports')}>Open reports</button>
  </div>
</section>

        {loading && (
          <p className="status-message loading-message" role="status">
            Loading candidate data...
          </p>
        )}

        {error && (
          <div className="status-message error-message" role="alert">
            <span>{error}</span>
            <button type="button" onClick={loadCandidates}>Try again</button>
          </div>
        )}

        {importNotice && (
  <div className="status-message loading-message" role="status">
    <span>{importNotice}</span>
    <button type="button" className="row-btn" onClick={() => setImportNotice('')}>
      Dismiss
    </button>
  </div>
)}

<section
  className={`upload-panel ${dragActive ? 'drag' : ''} ${uploading ? 'busy' : ''}`}
  onDragOver={(event) => {
    event.preventDefault()
    setDragActive(true)
  }}
  onDragLeave={() => setDragActive(false)}
  onDrop={(event) => {
    event.preventDefault()
    setDragActive(false)
    handleResumeFiles(event.dataTransfer.files)
  }}
>
  <div className="upload-icon" aria-hidden="true">
    <Icon name="upload" size={26} />
  </div>

  <div className="upload-text">
    <h3>{uploading ? 'Reading resumes...' : 'Drop resumes here to rank them instantly'}</h3>
    <p>
      PDF files only. Each resume is read, matched against every open position
      and added to your leaderboard.
    </p>
  </div>

  <label className="upload-btn">
    Choose PDFs
    <input
      type="file"
      accept="application/pdf,.pdf"
      multiple
      disabled={uploading}
      onChange={(event) => {
        handleResumeFiles(event.target.files)
        event.target.value = ''
      }}
    />
  </label>

  {uploading && (
    <div className="upload-progress" aria-hidden="true"><i /></div>
  )}

  {uploadResult && (
    <div className="upload-result" role="status">
      {uploadResult.error ? (
        <span className="result-bad">{uploadResult.error}</span>
      ) : (
        <>
          {(uploadResult.added || []).map((item) => (
            <span className="result-good" key={`add-${item.file}`}>
              ✓ {item.name} added{item.email ? '' : ' (no email found)'}
            </span>
          ))}
          {[
            ...(uploadResult.skipped || []),
            ...(uploadResult.failed || []),
            ...(uploadResult.rejected || []),
          ].map((item) => (
            <span className="result-bad" key={`bad-${item.file}`}>
              ! {item.file}: {item.reason}
            </span>
          ))}
          {!(uploadResult.added || []).length &&
            !(uploadResult.skipped || []).length &&
            !(uploadResult.failed || []).length &&
            !(uploadResult.rejected || []).length && (
              <span className="result-good">Nothing new to add.</span>
            )}
        </>
      )}
    </div>
  )}
</section>
        {!loading && !error && (
          <>
            <section className="stats-grid" aria-label="Recruitment statistics">
  {[
    { label: 'Total Candidates', value: candidates.length, note: 'Candidate match records', icon: 'candidates', tone: 'blue' },
    { label: 'Shortlisted', value: shortlisted, note: 'Marked by the recruiter', icon: 'check', tone: 'green' },
    { label: 'Scheduled Interviews', value: scheduledCount, note: 'Upcoming sessions', icon: 'clock', tone: 'purple' },
    { label: 'Completed Interviews', value: completedCount, note: `${cancelledCount} cancelled`, icon: 'calendar', tone: 'orange' },
  ].map((card) => (
    <article className="stat-card" key={card.label}>
      <div className="stat-card-top">
        <span>{card.label}</span>
        <span className={`stat-icon icon-${card.tone}`}><Icon name={card.icon} /></span>
      </div>
            <h2><CountUp value={card.value} /></h2>
      <p>{card.note}</p>
    </article>
  ))}
</section>

<section className="pipeline" aria-label="Hiring pipeline">
  {[
    { label: 'Candidates', value: candidates.length },
    { label: 'Shortlisted', value: shortlisted },
    { label: 'Interviews booked', value: scheduledCount + completedCount },
    { label: 'Interviews completed', value: completedCount },
  ].map((step, index) => {
    const percent = candidates.length
      ? Math.min(100, Math.round((step.value / candidates.length) * 100))
      : 0

    return (
      <div className="pipeline-step" key={step.label}>
        <div className="pipeline-top">
          <span>{step.label}</span>
          <em>{index === 0 ? '' : `${percent}%`}</em>
        </div>
        <strong>{step.value}</strong>
        <div className="pipeline-bar">
          <i style={{ width: `${index === 0 ? 100 : percent}%` }} />
        </div>
      </div>
    )
  })}
</section>

{jobTitles.length > 0 && (
  <section className="table-card top-matches">
    <div className="table-heading">
      <div>
        <h2>Top Matches</h2>
        <p>The best-fitting candidates for each position, ready to shortlist.</p>
      </div>
    </div>

    <div className="status-tabs" role="group" aria-label="Choose a job position">
      {jobTitles.map((title) => (
        <button
          key={title}
          type="button"
          className={`status-tab ${topJob === title ? 'active' : ''}`}
          onClick={() => setTopJobTab(title)}
          aria-pressed={topJob === title}
        >
          {title}
        </button>
      ))}
    </div>

    <div className="top-grid">
      {topMatches.map((candidate, index) => {
        const score = Number(candidate.skill_match_score_percent ?? 0)
        const decision = candidate.recruiter_decision || 'Not Decided'

        return (
          <article
            className="top-card"
            key={`${candidate.candidate_email}-${candidate.job_title}-${index}`}
          >
            <span className="rank-badge">#{index + 1}</span>

            <div className="top-card-head">
              <div className="candidate-avatar">
                {(candidate.candidate_name || '?').charAt(0).toUpperCase()}
              </div>
              <div className="candidate-details">
                <strong>{candidate.candidate_name || 'Unknown'}</strong>
                <span>{candidate.candidate_email || 'No email available'}</span>
              </div>
            </div>

            <div className="top-score">
              <strong>{score}%</strong>
              <span>skill match</span>
            </div>
            <div className="score-bar">
              <i style={{ width: `${Math.min(score, 100)}%` }} />
            </div>

            <div className="tag-row">
              {(candidate.matched_skills || []).slice(0, 5).map((skill) => (
                <span className="tag tag-ok" key={`ok-${skill}`}>{skill}</span>
              ))}
              {(candidate.missing_skills || []).slice(0, 3).map((skill) => (
                <span className="tag tag-miss" key={`miss-${skill}`}>− {skill}</span>
              ))}
            </div>

            <div className="top-card-actions">
              {decision === 'Shortlisted' ? (
                <span className="chip chip-today">✓ Shortlisted</span>
              ) : (
                <button
                  type="button"
                  className="schedule-interview-button"
                  onClick={() => handleDecisionChange(candidate, 'Shortlisted')}
                >
                  Shortlist
                </button>
              )}
              <button
                type="button"
                className="row-btn"
                onClick={() => openAiInsights(candidate)}
              >
                Insights
              </button>
            </div>
          </article>
        )
      })}
    </div>

    <p className="table-note">
      Green tags are matched skills. Orange tags marked with a minus are missing skills.
    </p>
  </section>
)}

            <section className="table-card">
              <div className="table-heading">
                <div>
                  <h2>Candidate Matching Results</h2>
                  <p>Review skill matches and recruitment decisions.</p>
                </div>
                <button
                  type="button"
                  className="refresh-button"
                  onClick={syncResumes}
                  disabled={refreshing}
                  aria-label="Refresh candidate data"
                  title="Refresh candidate data"
                >
                  <span className={refreshing ? 'refresh-icon spinning' : 'refresh-icon'}>
                    ↻
                  </span>
                </button>
              </div>

              <div className="candidate-toolbar">
                <div className="search-container">
                  <span className="search-icon" aria-hidden="true">⌕</span>
                  <input
                    type="search"
                    className="candidate-search"
                    placeholder="Search by name or email..."
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    aria-label="Search candidates"
                  />
                  {searchTerm && (
                    <button
                      type="button"
                      className="clear-search-button"
                      onClick={() => setSearchTerm('')}
                      aria-label="Clear search"
                      title="Clear search"
                    >
                      ×
                    </button>
                  )}
                </div>
                <select
  className="job-filter"
  value={jobFilter}
  onChange={(event) => setJobFilter(event.target.value)}
  aria-label="Filter by job position"
>
  <option value="all">All Job Positions</option>
  {jobTitles.map((title) => (
    <option key={title} value={title}>
      {title}
    </option>
  ))}
</select>

<Toggle checked={shortlistedOnly} onChange={setShortlistedOnly} label="Shortlisted only" />
<Toggle checked={compactRows} onChange={setCompactRows} label="Compact rows" />

                <p className="candidate-count" aria-live="polite">
                  Showing <strong>{filteredCandidates.length}</strong> of{' '}
                  <strong>{candidates.length}</strong> records
                </p>
              </div>

              {filteredCandidates.length === 0 ? (
                <div className="empty-state">
                  <span className="empty-state-icon">⌕</span>
                  <strong>No candidates found</strong>
                  <span>Try another name or email address.</span>
                </div>
              ) : (
                <div className={`table-wrapper ${compactRows ? 'compact' : ''}`}>
                  <table>
                    <thead>
                      <tr>
                        <th>Candidate</th>
                        <th>Job Position</th>
                        <th>Skill Match</th>
                        <th>Skills Details</th>
                        <th>Decision</th>
                        <th>Recruitment Status</th>
                        <th>Interview</th>
                        <th>Email / AI</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredCandidates.map((candidate, index) => (
                        <tr
                          key={`${candidate.candidate_email}-${candidate.job_title}-${index}`}
                        >
                          <td>
                            <div className="candidate-cell">
                              <div className="candidate-avatar">
                                {(candidate.candidate_name || '?').charAt(0).toUpperCase()}
                              </div>
                              <div className="candidate-details">
                                <strong>{candidate.candidate_name || 'Unknown'}</strong>
                                <span>{candidate.candidate_email || 'No email available'}</span>
                              </div>
                            </div>
                          </td>
                          <td>{candidate.job_title || 'Not specified'}</td>
                          <td><ScoreRing value={candidate.skill_match_score_percent} /></td>
                          <td>
  <div className="skill-chips">
    {(candidate.matched_skills || []).map((skill) => (
      <span className="tag tag-ok" key={`ok-${skill}`}>{skill}</span>
    ))}
    {(candidate.missing_skills || []).map((skill) => (
      <span className="tag tag-miss" key={`miss-${skill}`}>− {skill}</span>
    ))}
    {!(candidate.matched_skills?.length || candidate.missing_skills?.length) && (
      <span className="muted-text">No skills reported</span>
    )}
  </div>
</td>
                          <td>


<select
  className="decision-select"
  value={candidate.recruiter_decision || 'Not Decided'}
  onChange={(event) =>
    handleDecisionChange(candidate, event.target.value)
  }
  aria-label={`Decision for ${candidate.candidate_name || 'candidate'}`}
>
  <option value="Not Decided">Not Decided</option>
  <option value="Under Review">Under Review</option>
  <option value="Shortlisted">Shortlisted</option>
  <option value="Rejected">Rejected</option>
</select>

                          </td>
                          <td>
                            <span className={`status-badge ${
                              candidate.recruitment_status === 'Interview Scheduled'
                                ? 'badge-info'
                                : candidate.recruitment_status === 'Selected'
                                  ? 'badge-success'
                                  : candidate.recruitment_status === 'Rejected'
                                    ? 'badge-danger'
                                    : 'badge-neutral'
                            }`}>
                              {candidate.recruitment_status || 'Not Set'}
                            </span>
                          </td>
                          <td>
  <button
    type="button"
    className="schedule-interview-button"
    onClick={() => {
      setSelectedCandidate(candidate)
      setShowInterviewForm(true)
    }}
  >
    Schedule Interview
  </button>
</td>
                          <td>
  <div className="row-actions">
    <button
      type="button"
      className="send-email-button"
      onClick={() => openEmailComposer(candidate)}
    >
      <span aria-hidden="true">✉</span> Send Email
    </button>
    <button
      type="button"
      className="ai-btn"
      onClick={() => openAiInsights(candidate)}
    >
      ✦ Smart Insights
    </button>
  </div>
</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <p className="table-note">
                Match scores support recruiter review; they are not automatic
                hiring decisions. Skill details depend on the data returned by
                the backend.
              </p>
            </section>

{showInterviewForm && (
  <div className="interview-modal">
    <form
      className="interview-form"


onSubmit={async (event) => {
  event.preventDefault()

  try {
    if (editingInterview) {
      await editInterview(editingInterview.id, {
        date: interviewDate,
        time: interviewTime,
        duration: Number(interviewDuration),
        mode: interviewMode,
        notes: interviewNotes,
      })

      setScheduledInterviews((previous) =>
        previous.map((item) =>
          item.id === editingInterview.id
            ? {
                ...item,
                date: interviewDate,
                time: interviewTime,
                duration: Number(interviewDuration),
                mode: interviewMode,
                notes: interviewNotes,
              }
            : item
        )
      )

      window.alert('Interview updated successfully!')
    } else {
      if (!selectedCandidate) {
        window.alert('Please select a candidate first.')
        return
      }

      const savedInterview = await createInterview({
        candidate_name: selectedCandidate.candidate_name || '',
        candidate_email: selectedCandidate.candidate_email || '',
        job_title: selectedCandidate.job_title || '',
        date: interviewDate,
        time: interviewTime,
        duration: Number(interviewDuration),
        mode: interviewMode,
        notes: interviewNotes,
      })

            setScheduledInterviews((previous) =>
        keepLatestPerCandidate([savedInterview, ...previous])
      )

      window.alert('Interview saved successfully!')
    }

    setShowInterviewForm(false)
    setSelectedCandidate(null)
    setEditingInterview(null)
    setInterviewDate('')
    setInterviewTime('')
    setInterviewDuration('30')
    setInterviewMode('Online')
    setInterviewNotes('')
  } catch (error) {
    window.alert(error.message || 'Could not save the interview.')
  }
}}

    >
      <h2>{editingInterview ? 'Edit Interview' : 'Schedule Interview'}</h2>
      <p>
        Candidate: {editingInterview?.candidate_name || selectedCandidate?.candidate_name}
      </p>

      <label>
        Interview Date
        <input
          type="date"
          value={interviewDate}
          onChange={(event) => setInterviewDate(event.target.value)}
          required
        />
      </label>

      <label>
        Interview Time
        <input
          type="time"
          value={interviewTime}
          onChange={(event) => setInterviewTime(event.target.value)}
          required
        />
      </label>

      <label>
        Duration
        <select
          value={interviewDuration}
          onChange={(event) => setInterviewDuration(event.target.value)}
        >
          <option value="15">15 minutes</option>
          <option value="30">30 minutes</option>
          <option value="45">45 minutes</option>
          <option value="60">60 minutes</option>
        </select>
      </label>

      <label>
        Interview Mode
        <select
          value={interviewMode}
          onChange={(event) => setInterviewMode(event.target.value)}
        >
          <option value="Online">Online</option>
          <option value="In Person">In Person</option>
        </select>
      </label>

      <label>
        Notes
        <textarea
          value={interviewNotes}
          onChange={(event) => setInterviewNotes(event.target.value)}
          placeholder="Enter interview instructions or notes"
        />
      </label>

      <div className="interview-form-actions">
        <button
  type="button"
  onClick={() => {
    setShowInterviewForm(false)
    setSelectedCandidate(null)
    setEditingInterview(null)
  }}
>
  Cancel
</button>
        <button type="submit">Save Interview</button>
      </div>
    </form>
  </div>
)}




{/* STEP 5: SCHEDULED INTERVIEWS */}
<section className="table-card scheduled-interviews">
  <div className="table-heading">
    <div>
      <h2>Scheduled Interviews</h2>
      <p>Track, update and manage every interview in one place.</p>
    </div>
    <span className="interview-count">
  {filteredInterviews.length} of {visibleInterviews.length}
</span>
  </div>

  <div className="interview-toolbar">
    <Toggle checked={upcomingOnly} onChange={setUpcomingOnly} label="Upcoming only" />
    <div className="search-container">
      <span className="search-icon" aria-hidden="true">⌕</span>
      <input
        type="search"
        className="candidate-search"
        placeholder="Search candidate, email or job..."
        value={interviewSearch}
        onChange={(event) => setInterviewSearch(event.target.value)}
        aria-label="Search interviews"
      />
      {interviewSearch && (
        <button
          type="button"
          className="clear-search-button"
          onClick={() => setInterviewSearch('')}
          aria-label="Clear search"
        >
          ×
        </button>
      )}
    </div>

    <div className="status-tabs" role="group" aria-label="Filter interviews by status">
      {statusTabs.map((tab) => (
        <button
          key={tab}
          type="button"
          className={`status-tab ${interviewStatusFilter === tab ? 'active' : ''}`}
          onClick={() => setInterviewStatusFilter(tab)}
          aria-pressed={interviewStatusFilter === tab}
        >
          {tab}
          <span>{statusCount(tab)}</span>
        </button>
      ))}
    </div>
  </div>

  {visibleInterviews.length === 0 ? (
  <div className="empty-state">
    <strong>
      {upcomingOnly && scheduledInterviews.length > 0
        ? 'No upcoming interviews'
        : 'No interviews scheduled yet'}
    </strong>
    <span>
      {upcomingOnly && scheduledInterviews.length > 0
        ? 'Past interviews are hidden. Turn off "Upcoming only" to see them, or schedule a new one.'
        : 'Click Schedule Interview beside a candidate to create one.'}
    </span>
  </div>
) : filteredInterviews.length === 0 ? (
    <div className="empty-state">
      <strong>No interviews match your filters</strong>
      <span>Try a different search or status.</span>
      <button
        type="button"
        className="row-btn"
        onClick={() => {
          setInterviewSearch('')
          setInterviewStatusFilter('All')
        }}
      >
        Clear filters
      </button>
    </div>
  ) : (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>When</th>
            <th>Candidate</th>
            <th>Position</th>
            <th>Format</th>
            <th>Notes</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredInterviews.map((interview, index) => {
            const status = interview.status || 'Scheduled'
            const when = formatInterviewDate(interview.date)
            const isToday = interview.date === todayKey
            const pastDue = status === 'Scheduled' && interview.date && interview.date < todayKey

            return (
              <tr
                key={interview.id || `${interview.candidate_email}-${interview.date}-${interview.time}-${index}`}
                className={`interview-row status-${status.toLowerCase()}`}
              >
                <td>
                  <div className="when-cell">
                    <div className="date-block">
                      <strong>{when.day}</strong>
                      <span>{when.month}</span>
                    </div>
                    <div className="when-text">
                      <strong>{formatInterviewTime(interview.time)}</strong>
                      <span>{when.weekday}</span>
                      {isToday && status === 'Scheduled' && <em className="chip chip-today">Today</em>}
                      {pastDue && <em className="chip chip-pastdue">Past due</em>}
                    </div>
                  </div>
                </td>

                <td>
                  <div className="candidate-cell">
                    <div className="candidate-avatar">
                      {(interview.candidate_name || '?').charAt(0).toUpperCase()}
                    </div>
                    <div className="candidate-details">
                      <strong>{interview.candidate_name || 'Unknown'}</strong>
                      <span>{interview.candidate_email}</span>
                    </div>
                  </div>
                </td>

                <td>{interview.job_title || 'Not specified'}</td>

                <td>
                  <div className="format-cell">
                    <span className={`chip ${interview.mode === 'In Person' ? 'chip-inperson' : 'chip-online'}`}>
                      {interview.mode || 'Online'}
                    </span>
                    <small>{interview.duration || 30} min</small>
                  </div>
                </td>

                <td>
                  <div
                    className={`notes-cell ${interview.notes ? '' : 'empty'}`}
                    title={interview.notes || ''}
                  >
                    {interview.notes || '—'}
                  </div>
                </td>

                <td>
                  <select
                    value={status}
                    onChange={(event) =>
                      handleInterviewStatusChange(interview, event.target.value)
                    }
                    aria-label={`Status for ${interview.candidate_name || 'candidate'}`}
                  >
                    <option value="Scheduled">Scheduled</option>
                    <option value="Completed">Completed</option>
                    <option value="Cancelled">Cancelled</option>
                  </select>
                </td>

                <td>
                  <div className="row-actions">
                    <button
                      type="button"
                      className="row-btn"
                      disabled={status === 'Cancelled'}
                      onClick={() => {
                        setEditingInterview(interview)
                        setSelectedCandidate(null)
                        setInterviewDate(interview.date || '')
                        setInterviewTime(interview.time || '')
                        setInterviewDuration(String(interview.duration || 30))
                        setInterviewMode(interview.mode || 'Online')
                        setInterviewNotes(interview.notes || '')
                        setShowInterviewForm(true)
                      }}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="row-btn"
                      onClick={() => setEmailPreviewInterview(interview)}
                    >
                      Preview email
                    </button>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )}
</section>
          </>

        )}



{emailComposer && (
  <div className="interview-modal" role="presentation">
    <form className="interview-form email-composer-form" onSubmit={handleSaveTestEmail}>
      <div className="email-composer-heading">
        <div>
          <p className="email-mode-label">TEST MODE · NO REAL EMAIL SENT</p>
          <h2>Interview Invitation Email</h2>
          <p className="email-form-description">Edit the candidate details and message, then save it as a test email.</p>
        </div>
        <button type="button" className="email-close-button" onClick={() => setEmailComposer(null)} aria-label="Close email editor">×</button>
      </div>

      <div className="email-form-grid">
        <label>
          Candidate Name
          <input value={emailComposer.candidate_name} onChange={(event) => updateEmailDraftField('candidate_name', event.target.value)} required />
        </label>
        <label>
          Candidate Email (test text only)
          <input type="email" value={emailComposer.candidate_email} onChange={(event) => updateEmailDraftField('candidate_email', event.target.value)} required />
        </label>
        <label>
          Job Position
          <input value={emailComposer.job_title} onChange={(event) => updateEmailDraftField('job_title', event.target.value)} required />
        </label>
        <label>
          Email Subject
          <input value={emailComposer.subject} onChange={(event) => updateEmailDraftField('subject', event.target.value)} required />
        </label>
        <label>
          Interview Date
          <input type="date" value={emailComposer.interview_date} onChange={(event) => updateEmailDraftField('interview_date', event.target.value)} />
        </label>
        <label>
          Interview Time
          <input type="time" value={emailComposer.interview_time} onChange={(event) => updateEmailDraftField('interview_time', event.target.value)} />
        </label>
        <label>
          Duration
          <select value={emailComposer.duration} onChange={(event) => updateEmailDraftField('duration', event.target.value)}>
            <option value="15">15 minutes</option>
            <option value="30">30 minutes</option>
            <option value="45">45 minutes</option>
            <option value="60">60 minutes</option>
          </select>
        </label>
        <label>
          Interview Mode
          <select value={emailComposer.mode} onChange={(event) => updateEmailDraftField('mode', event.target.value)}>
            <option value="Online">Online</option>
            <option value="In Person">In Person</option>
          </select>
        </label>
      </div>

      <label className="email-body-label">
        Email Message
        <textarea rows="10" value={emailComposer.body} onChange={(event) => updateEmailDraftField('body', event.target.value)} required />
      </label>

      {testEmailMessage && (
        <div className={`email-test-result ${testEmailMessage.toLowerCase().includes('could not') ? 'email-test-error' : ''}`} role="status">
          {testEmailMessage}
        </div>
      )}

      <div className="email-composer-actions">
        <button type="button" className="email-cancel-button" onClick={() => setEmailComposer(null)}>Close</button>
        <button type="submit" className="send-email-button" disabled={savingTestEmail}>
          {savingTestEmail ? 'Saving Test...' : 'Save as Test Sent'}
        </button>
      </div>
      <p className="email-test-note">This is a local test record only. RecruitAI will not connect to Gmail or deliver this message.</p>
    </form>
  </div>
)}

{aiCandidate && (
  <div className="interview-modal" role="presentation">
    <div className="interview-form ai-modal" role="dialog" aria-modal="true" aria-label="AI candidate insights">
      <div className="email-composer-heading">
        <div>
          <p className="ai-label">✦ SMART INSIGHTS · ADVISORY ONLY</p>
          <h2>{aiCandidate.candidate_name || 'Candidate'}</h2>
          <p className="email-form-description">
            {aiCandidate.job_title} · {Number(aiCandidate.skill_match_score_percent ?? 0)}% skill match
          </p>
        </div>
        <button type="button" className="email-close-button" onClick={closeAiInsights} aria-label="Close AI insights">×</button>
      </div>

      {aiLoading && <p className="status-message loading-message" role="status">Analysing candidate...</p>}
      {aiError && <div className="email-test-result email-test-error" role="alert">{aiError}</div>}

      {aiInsights && (
        <>
          <p className="ai-summary">{aiInsights.summary}</p>

          <div className="ai-columns">
            <div>
              <h4>Strengths</h4>
              <ul>{aiInsights.strengths.map((item, i) => <li key={i}>{item}</li>)}</ul>
            </div>
            <div>
              <h4>Gaps to explore</h4>
              <ul>{aiInsights.gaps.map((item, i) => <li key={i}>{item}</li>)}</ul>
            </div>
          </div>

          <h4>Suggested interview questions</h4>
          <ol className="ai-questions">
            {aiInsights.interview_questions.map((q, i) => <li key={i}>{q}</li>)}
          </ol>

          <p className="email-test-note">
  These suggestions are generated from the candidate's matched and missing skills.
  They support, and never replace, recruiter judgement. Nothing is sent outside your computer.
</p>
        </>
      )}
    </div>
  </div>
)}

{emailPreviewInterview && (
  <div className="interview-modal">
    <div className="interview-form">
      <h2>Interview Email Preview</h2>

      <p>
        <strong>To:</strong>{" "}
        {emailPreviewInterview.candidate_email || "candidate@example.com"}
      </p>

      <p>
        <strong>Subject:</strong> Interview Scheduled —{" "}
        {emailPreviewInterview.job_title || "Job Position"}
      </p>

      <hr />

      <p>
        Dear {emailPreviewInterview.candidate_name || "Candidate"},
      </p>

      <p>Your interview has been scheduled successfully.</p>

      <p><strong>Date:</strong> {emailPreviewInterview.date}</p>
      <p><strong>Time:</strong> {emailPreviewInterview.time}</p>
      <p><strong>Duration:</strong> {emailPreviewInterview.duration} minutes</p>
      <p><strong>Mode:</strong> {emailPreviewInterview.mode}</p>

      <p>
        Best regards,<br />
        RecruitAI Recruitment Team
      </p>

      <p><strong>Demo only — no email has been sent.</strong></p>

      <button
        type="button"
        className="schedule-interview-button"
        onClick={() => setEmailPreviewInterview(null)}
      >
        Close Preview
      </button>
    </div>
  </div>
)}
  </>
)}

{paletteOpen && (
  <div className="cmd-overlay" role="presentation" onClick={() => setPaletteOpen(false)}>
    <div
      className="cmd-panel"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
      onClick={(event) => event.stopPropagation()}
    >
      <div className="cmd-input-row">
        <Icon name="matching" size={18} />
        <input
          autoFocus
          className="cmd-input"
          placeholder="Type a command or search a candidate..."
          value={paletteQuery}
          onChange={(event) => {
            setPaletteQuery(event.target.value)
            setPaletteIndex(0)
          }}
          onKeyDown={(event) => {
            if (event.key === 'ArrowDown') {
              event.preventDefault()
              setPaletteIndex((index) => Math.min(index + 1, paletteResults.length - 1))
            }
            if (event.key === 'ArrowUp') {
              event.preventDefault()
              setPaletteIndex((index) => Math.max(index - 1, 0))
            }
            if (event.key === 'Enter') {
              event.preventDefault()
              runPaletteItem(paletteResults[paletteIndex])
            }
          }}
          aria-label="Search commands and candidates"
        />
        <kbd>Esc</kbd>
      </div>

      <div className="cmd-list" role="listbox">
        {paletteResults.length === 0 ? (
          <p className="cmd-empty">No results for &quot;{paletteQuery}&quot;</p>
        ) : (
          paletteResults.map((item, index) => (
            <button
              key={item.id}
              type="button"
              role="option"
              aria-selected={index === paletteIndex}
              className={`cmd-item ${index === paletteIndex ? 'active' : ''}`}
              ref={(element) => {
                if (element && index === paletteIndex) {
                  element.scrollIntoView({ block: 'nearest' })
                }
              }}
              onMouseEnter={() => setPaletteIndex(index)}
              onClick={() => runPaletteItem(item)}
            >
              <span>{item.label}</span>
              <em>{item.hint}</em>
            </button>
          ))
        )}
      </div>

      <div className="cmd-footer">
        <span><kbd>↑</kbd><kbd>↓</kbd> move</span>
        <span><kbd>Enter</kbd> run</span>
        <span><kbd>Esc</kbd> close</span>
      </div>
    </div>
  </div>
)}

{showJobForm && (
  <div className="interview-modal" role="presentation">
    <form className="interview-form job-form" onSubmit={handleCreateJob}>
      <div className="email-composer-heading">
        <div>
          <p className="ai-label">NEW POSITION</p>
          <h2>Add a job position</h2>
          <p className="email-form-description">
            Every candidate is matched against it automatically.
          </p>
        </div>
        <button type="button" className="email-close-button" onClick={closeJobForm} aria-label="Close">×</button>
      </div>

      <label>
        Job title
        <input
          value={newJobTitle}
          onChange={(event) => setNewJobTitle(event.target.value)}
          placeholder="e.g. Cloud Engineer"
          maxLength={80}
          required
        />
      </label>

      <div className="field">
        <span className="field-label">Required skills</span>
        <div className="skill-entry">
          {newJobSkills.map((skill) => (
            <button
              type="button"
              className="tag tag-ok removable"
              key={skill}
              onClick={() => setNewJobSkills((previous) => previous.filter((item) => item !== skill))}
              aria-label={`Remove ${skill}`}
            >
              {skill} ×
            </button>
          ))}
          <input
            value={skillInput}
            onChange={(event) => setSkillInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ',') {
                event.preventDefault()
                addJobSkill(skillInput)
              }
            }}
            placeholder="Type a skill, press Enter"
            aria-label="Add a required skill"
          />
        </div>

        <div className="skill-suggest">
          {KNOWN_SKILLS
            .filter((skill) => !newJobSkills.some((item) => item.toLowerCase() === skill.toLowerCase()))
            .map((skill) => (
              <button type="button" key={skill} onClick={() => addJobSkill(skill)}>
                + {skill}
              </button>
            ))}
        </div>
        <p className="email-test-note">
          Skills outside the suggestions can be added, but no candidate will match them
          until the resume reader learns them.
        </p>
      </div>

      {jobError && <div className="email-test-result email-test-error" role="alert">{jobError}</div>}

      <div className="interview-form-actions">
        <button type="button" onClick={closeJobForm}>Cancel</button>
        <button type="submit" disabled={jobSaving}>
          {jobSaving ? 'Matching candidates...' : 'Add position'}
        </button>
      </div>
    </form>
  </div>
)}

      </main>
    </div>
  )
}

export default App
