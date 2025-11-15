# Product Requirements Document: TidyDownloads

**Version:** 1.0  
**Date:** November 15, 2025  
**Status:** Draft  
**Owner:** Hang

---

## 1. Executive Summary

**Product Name:** TidyDownloads

**Vision:** A lightweight macOS menu bar app that automatically organizes the Downloads folder on a weekly schedule, keeping recent files accessible while maintaining a clean, predictable folder structure.

**Target Users:** 
- Mac users who accumulate files in Downloads folder
- Professionals who download frequently (documents, installers, images)
- Anyone frustrated by cluttered Downloads folder

**Key Differentiation:**
- Hands-off weekly automation (not real-time)
- Keeps recent downloads (< 7 days) untouched and accessible
- Native macOS menu bar integration
- Simple, predictable organization rules
- Special handling for installer files

---

## 2. Problem Statement

### User Pain Points
1. Downloads folder becomes cluttered within days/weeks
2. Finding downloaded files becomes time-consuming
3. Manual organization is tedious and often forgotten
4. Existing tools either organize too aggressively (move everything immediately) or require constant manual intervention
5. Installer files (.dmg, .pkg) clutter the folder and are rarely deleted after use

### Current Solutions & Gaps
- **Hazel ($42):** Too expensive for casual users, overkill for simple needs
- **Folder Tidy ($3):** Requires manual triggering, no scheduling
- **Sparkle (AI-based):** Over-engineered, privacy concerns with file name analysis
- **Manual organization:** Requires discipline, often forgotten

---

## 3. Goals & Objectives

### Primary Goals
1. Reduce time spent searching for files in Downloads
2. Maintain a clean Downloads folder with minimal user effort
3. Provide predictable, reversible organization
4. Keep the tool simple and lightweight

### Success Metrics
- **Adoption:** 1,000 active users in first 3 months
- **Engagement:** Users run the app for 3+ weeks consecutively
- **Satisfaction:** 4+ star rating on feedback
- **Performance:** Organize 1,000 files in < 5 seconds

### Non-Goals (Out of Scope for MVP)
- Organization of other folders (Desktop, Documents)
- AI-powered smart categorization
- Cloud sync integration
- Advanced rule customization UI
- File tagging or renaming

---

## 4. User Stories

### Core User Stories

**As a professional user:**
- I want my Downloads folder to stay clean without thinking about it
- I need recent downloads to stay easily accessible in the main folder
- I want to quickly see what was organized and when
- I need to be able to undo organization if something goes wrong

**As a developer:**
- I want installer files (.dmg, .pkg) automatically separated from other downloads
- I need installers to be kept for easy reinstallation but not clutter my main view
- I want to bulk-delete old installers when needed

**As a casual user:**
- I want a simple "set and forget" solution
- I need to know the app is working without checking constantly
- I want to manually trigger organization when needed
- I need confidence that my files won't be lost or deleted

---

## 5. Features & Requirements

### 5.1 Core Features (MVP)

#### Feature 1: Automated Weekly Organization
**Priority:** P0 (Must Have)

**Description:** Automatically organize Downloads folder every week at a scheduled time.

**Requirements:**
- Run every Sunday at 2:00 AM by default
- Only process files older than 7 days (configurable)
- Use macOS launchd for scheduling
- Continue working even if app is not actively running
- Send macOS notification after completion

**Acceptance Criteria:**
- [ ] Schedule is installed during app setup
- [ ] Organization runs automatically at configured time
- [ ] Files < 7 days old remain in Downloads folder
- [ ] User receives notification with summary (X files organized)
- [ ] Works even when Mac wakes from sleep

---

#### Feature 2: Smart File Categorization
**Priority:** P0 (Must Have)

**Description:** Categorize files into logical folders based on file type and purpose.

**Organization Categories:**

| Category | Subfolder Name | File Types | Examples |
|----------|---------------|------------|----------|
| **Installers** | `_Installers` | .dmg, .pkg, .app (zipped apps) | Chrome.dmg, Spotify.pkg |
| **Documents** | `_Documents` | .pdf, .doc, .docx, .txt, .rtf, .pages, .xlsx, .csv, .ppt | report.pdf, invoice.xlsx |
| **Images** | `_Images` | .jpg, .jpeg, .png, .gif, .svg, .heic, .webp | photo.jpg, screenshot.png |
| **Videos** | `_Videos` | .mp4, .mov, .avi, .mkv, .webm | video.mp4, recording.mov |
| **Audio** | `_Audio` | .mp3, .m4a, .wav, .aac, .flac | song.mp3, podcast.m4a |
| **Archives** | `_Archives` | .zip, .rar, .7z, .tar, .gz | backup.zip, files.tar.gz |
| **Code** | `_Code` | .json, .yaml, .xml, .py, .js, .swift | config.json, script.py |
| **Other** | `_Other` | All other file types | unknown.xyz |

**Additional Rules:**
- Folders/directories are never moved (user-created folders stay)
- Hidden files (starting with `.`) are ignored
- Files in use/locked are skipped with warning
- Prefix subfolders with `_` to sort to top in Finder

**Acceptance Criteria:**
- [ ] All specified file types are correctly categorized
- [ ] Unknown file types go to `_Other`
- [ ] User-created folders in Downloads are not touched
- [ ] Hidden files and system files are ignored
- [ ] Categories can be disabled via config

---

#### Feature 3: Menu Bar Application
**Priority:** P0 (Must Have)

**Description:** Native macOS menu bar app providing quick access and status overview.

**Menu Items:**
```
🗂️ TidyDownloads
├─ Last organized: 3 days ago
├─ Next scheduled: in 4 days
├─ ──────────────
├─ ▶️ Organize Now
├─ 👁️ Preview Organization (shows what would happen)
├─ ↩️ Undo Last Organization
├─ ──────────────
├─ ⚙️ Preferences...
├─ 📊 Show Statistics
├─ ❓ Help
└─ ⏏️ Quit TidyDownloads
```

**Requirements:**
- Lives in macOS menu bar (status bar)
- Shows icon with optional badge (number of files to organize)
- Updates status dynamically
- Opens at login (optional)
- Minimal memory footprint (< 50MB)

**Acceptance Criteria:**
- [ ] App appears in menu bar
- [ ] All menu items are functional
- [ ] Status updates reflect actual state
- [ ] Memory usage < 50MB when idle
- [ ] Responsive UI (no freezing)

---

#### Feature 4: Preview Mode
**Priority:** P1 (Should Have)

**Description:** Show users what will be organized before running.

**Requirements:**
- Display list of files to be organized
- Show source → destination for each file
- Group by category
- Show file count per category
- Allow user to proceed or cancel

**UI Mockup (Terminal/Dialog):**
```
Preview: 47 files will be organized

Installers (8):
  → _Installers/
    • Chrome.dmg (152 MB)
    • Spotify.pkg (89 MB)
    • VLC-3.0.dmg (45 MB)
    ...

Documents (23):
  → _Documents/
    • invoice_oct.pdf
    • report.docx
    ...

Images (12):
  → _Images/
    ...

[Proceed]  [Cancel]
```

**Acceptance Criteria:**
- [ ] Preview shows accurate file list
- [ ] Files are grouped by category
- [ ] Shows file size for large files
- [ ] User can cancel safely
- [ ] Preview runs quickly (< 1 second)

---

#### Feature 5: Undo Functionality
**Priority:** P1 (Should Have)

**Description:** Restore files to original locations after organization.

**Requirements:**
- Track all file moves in a manifest file
- Store last 5 organization sessions
- One-click undo from menu bar
- Undo is safe (checks if files still exist)
- Undo moves files back to exact original locations

**Technical Details:**
- Manifest stored in `~/Library/Application Support/TidyDownloads/history/`
- JSON format with timestamps and file mappings
- Auto-cleanup of old manifests (> 30 days)

**Acceptance Criteria:**
- [ ] Undo restores all files to original locations
- [ ] Undo works even after multiple organizations
- [ ] Warning if files have been modified/deleted
- [ ] Undo manifest persists across app restarts
- [ ] User can see what will be undone before confirming

---

#### Feature 6: Configuration & Preferences
**Priority:** P1 (Should Have)

**Description:** User-configurable settings for customization.

**Configurable Settings:**

| Setting | Default | Options | Description |
|---------|---------|---------|-------------|
| Schedule Day | Sunday | Mon-Sun, Disabled | Day to run organization |
| Schedule Time | 2:00 AM | 00:00-23:59 | Time to run organization |
| Minimum File Age | 7 days | 1-30 days | How old files must be before organizing |
| Enabled Categories | All | Checkboxes per category | Which categories to use |
| Send Notifications | Yes | Yes/No | macOS notifications after organization |
| Open at Login | No | Yes/No | Launch app at system startup |
| Downloads Path | ~/Downloads | Custom path | Folder to organize (future) |

**Storage:**
- Config file: `~/Library/Application Support/TidyDownloads/config.json`
- JSON format for easy editing
- Validated on load with fallback to defaults

**Acceptance Criteria:**
- [ ] All settings are persistent
- [ ] Changes take effect immediately or on next run
- [ ] Invalid values fallback to defaults
- [ ] Preferences UI is intuitive
- [ ] Settings file is human-readable

---

#### Feature 7: Statistics & Reporting
**Priority:** P2 (Nice to Have)

**Description:** Show users the impact of organization.

**Metrics to Track:**
- Total files organized (lifetime)
- Space analyzed
- Last organization date
- Files organized per category
- Average organization time

**Display:**
- Simple dialog/window with stats
- Exportable as JSON (for nerds)

**Acceptance Criteria:**
- [ ] Stats are accurate
- [ ] Stats persist across app restarts
- [ ] Display is clear and readable

---

### 5.2 Non-Functional Requirements

#### Performance
- Organize 1,000 files in < 5 seconds
- App startup time < 1 second
- Memory usage < 50MB when idle
- CPU usage < 5% when organizing

#### Reliability
- No data loss (files are moved, never deleted)
- Safe handling of locked/in-use files
- Graceful failure with user notification
- Undo capability for error recovery

#### Usability
- Zero configuration required to start
- Clear, jargon-free language
- Predictable behavior
- Discoverable features (tooltips)

#### Compatibility
- macOS 11 (Big Sur) and later
- Apple Silicon (M1/M2/M3) and Intel
- Python 3.9+ runtime

#### Security & Privacy
- No network access required
- No data collection or telemetry
- All processing happens locally
- Open source code for transparency

---

## 6. Technical Architecture

### Technology Stack
- **Language:** Python 3.9+
- **Menu Bar:** rumps (PyObjC wrapper)
- **Scheduling:** macOS launchd
- **File Ops:** pathlib, shutil
- **Config:** JSON
- **Packaging:** py2app
- **Logging:** Python logging module

### System Integration
```
┌─────────────────┐
│   macOS User    │
└────────┬────────┘
         │ interacts with
         ▼
┌─────────────────┐         ┌──────────────┐
│  Menu Bar App   │◄────────┤   rumps      │
│   (app.py)      │         └──────────────┘
└────────┬────────┘
         │ calls
         ▼
┌─────────────────┐         ┌──────────────┐
│   Organizer     │◄────────┤  pathlib/    │
│  (organizer.py) │         │  shutil      │
└────────┬────────┘         └──────────────┘
         │ uses
         ▼
┌─────────────────┐
│  Config Manager │
│(config_mgr.py)  │
└────────┬────────┘
         │ stores in
         ▼
┌─────────────────┐
│ ~/Library/App   │
│ Support/Tidy    │
│ Downloads/      │
└─────────────────┘

         ┌──────────────┐
         │   launchd    │◄─── Weekly trigger
         └──────┬───────┘
                │ executes
                ▼
         ┌──────────────┐
         │ organize.py  │
         │   (CLI)      │
         └──────────────┘
```

### File Operations
- All operations use `shutil.move()` (atomic on same filesystem)
- Collision handling: append `_2`, `_3`, etc. to filename
- Dry-run mode for preview
- Transaction log for undo capability

---

## 7. User Experience Flow

### First-Time Setup
1. User downloads and opens TidyDownloads.app
2. Welcome screen explains what the app does
3. User chooses schedule or manual mode
4. macOS permission request for Downloads folder access
5. App icon appears in menu bar
6. Optional: Enable "Open at Login"

### Weekly Automation Flow
1. launchd triggers `organize.py` at scheduled time
2. Script scans Downloads folder
3. Files > 7 days old are identified
4. Files are categorized and moved to subfolders
5. Manifest file is created for undo
6. macOS notification sent with summary
7. Menu bar icon badge updates

### Manual Organization Flow
1. User clicks "Organize Now" from menu
2. Preview window shows what will happen
3. User confirms or cancels
4. Organization runs with progress indicator
5. Notification shows completion
6. Menu updates to show last run time

### Undo Flow
1. User clicks "Undo Last Organization"
2. Confirmation dialog with preview
3. Files are moved back to original locations
4. Notification confirms undo
5. Manifest is marked as undone

---

## 8. Success Criteria

### MVP Launch Criteria
- [ ] App installs without errors
- [ ] Weekly scheduling works reliably
- [ ] All file categories organize correctly
- [ ] Undo successfully restores files
- [ ] No data loss in testing (1,000+ file test)
- [ ] Memory usage < 50MB
- [ ] Works on macOS 11+, Apple Silicon & Intel

### User Acceptance
- [ ] 90% of test users find it "easy to use"
- [ ] Users report cleaner Downloads folder
- [ ] No critical bugs in 2-week beta period

---

## 9. Development Roadmap

### Phase 1: Core Engine (Week 1-2)
- [ ] File categorization logic
- [ ] Organization engine
- [ ] Undo system
- [ ] Configuration system
- [ ] CLI version working

### Phase 2: Menu Bar App (Week 3)
- [ ] rumps integration
- [ ] Menu UI implementation
- [ ] Preview mode
- [ ] Preferences window

### Phase 3: Scheduling (Week 4)
- [ ] launchd plist generation
- [ ] Installation script
- [ ] Notification system
- [ ] Statistics tracking

### Phase 4: Polish & Testing (Week 5-6)
- [ ] Icon design
- [ ] Error handling
- [ ] Edge case testing
- [ ] User testing
- [ ] Documentation

### Phase 5: Distribution (Week 7)
- [ ] py2app packaging
- [ ] Code signing (if distributing)
- [ ] GitHub release
- [ ] README and documentation
- [ ] Beta distribution

---

## 10. Future Enhancements (Post-MVP)

### V2 Features
- Multiple folder support (Desktop, Documents)
- Custom organization rules
- Smart project detection (files downloaded together)
- Duplicate file detection
- Archive old files to compressed storage
- Keyboard shortcuts
- Dark mode icon

### Advanced Features
- Plugin system for custom rules
- Dropbox/Google Drive integration
- File preview in app
- Bulk file actions
- Advanced filtering (regex support)

---

## 11. Open Questions & Decisions Needed

1. **Icon Design:** What should the menu bar icon look like?
   - Suggestion: 📁 folder icon or 🗂️ file cabinet

2. **Notification Frequency:** When to notify users?
   - After every organization (current plan)
   - Only on errors?
   - User configurable?

3. **Installer Cleanup:** Should we auto-delete installers after X days?
   - Risk: User might need to reinstall
   - Benefit: Free up space automatically
   - Decision: NOT for MVP, maybe in V2 with user confirmation

4. **Duplicate Handling:** What if file already exists in destination?
   - Current plan: Append `_2`, `_3` to filename
   - Alternative: Ask user / Skip / Overwrite

5. **Launch at Login:** Default on or off?
   - Recommendation: Default OFF, user can enable

---

## 12. Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Data loss from buggy move operations | High | Low | Extensive testing, undo capability, never delete files |
| macOS permission issues | Medium | Medium | Clear permission request UX, fallback to manual mode |
| launchd scheduling unreliable | Medium | Low | Manual trigger always available, logging for debugging |
| Performance issues with many files | Medium | Medium | Async operations, progress indicators, optimization |
| User confusion about automation | Low | Medium | Clear onboarding, status always visible in menu bar |

---

## Appendix A: File Type Reference

### Installer File Types
```
.dmg  - Disk Image (most Mac installers)
.pkg  - Package installer
.app  - Application bundle (when zipped/downloaded)
.mpkg - Meta-package installer
```

### Document File Types
```
.pdf, .doc, .docx, .txt, .rtf, .odt
.xls, .xlsx, .csv, .numbers
.ppt, .pptx, .keynote, .pages
```

### Archive File Types
```
.zip, .rar, .7z, .tar, .gz, .bz2, .xz
```

### Code/Config File Types
```
.json, .yaml, .yml, .xml, .toml
.py, .js, .swift, .java, .cpp, .c
.md, .rst
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-15 | Hang | Initial PRD creation |