# ClockGuard Admin Dashboard - Frontend

Admin web dashboard for the ClockGuard facial recognition clock-in/out system.

## Scrum 6 Deliverable ✅

This is the foundational React project setup. The structure is designed to make upcoming tasks (Scrum 7-11) straightforward to implement.

## Tech Stack

- **React** - UI framework (JavaScript)
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing

## Project Structure

```
/frontend
├── src/
│   ├── assets/          # Logo and images (to be added in Scrum 7)
│   ├── components/      # Reusable components (Navbar, Sidebar - Scrum 9/11)
│   ├── pages/           # Page components
│   │   ├── LoginPage.jsx         # Minimal placeholder (full UI in Scrum 10)
│   │   └── DashboardPage.jsx     # Minimal placeholder (full layout in Scrum 11)
│   ├── routes/          # Router configuration
│   │   └── AppRouter.jsx         # Route definitions
│   ├── styles/          # Theme and global styles
│   │   ├── theme.js              # ClockGuard design tokens
│   │   └── global.css            # Global styles
│   ├── services/        # API and backend integration
│   │   └── apiClient.js          # API client placeholder
│   ├── App.jsx          # Root component
│   └── main.jsx         # Entry point
├── .env.example         # Environment variables template
└── .gitignore          # Git ignore rules
```

## Getting Started

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment variables (optional for now):**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values when backend is ready
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   - Navigate to `http://localhost:5173`
   - You should see the minimal login placeholder

## Available Routes

- `/` - Redirects to `/login`
- `/login` - Login page placeholder
- `/dashboard` - Dashboard page placeholder

## Next Sprints

- **Scrum 7:** Global branding (logo, colors, ClockGuard identity)
- **Scrum 9:** Navbar component (logo, logout button, responsive)
- **Scrum 10:** Complete login UI (form with email/password, sign-in button)
- **Scrum 11:** Dashboard shell (navbar + sidebar + content area, router redirect)

## Theme

The theme is defined in `src/styles/theme.js` with placeholder colors. These will be updated once the ClockGuard logo and brand identity are finalized in Scrum 7.

## API Integration

The `src/services/apiClient.js` file contains placeholder methods for future backend integration with:
- FastAPI backend endpoints
- Supabase authentication and data storage

## Build for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` directory.
