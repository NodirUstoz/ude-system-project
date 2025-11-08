document.addEventListener('DOMContentLoaded', () => {
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    const themeToggle = document.querySelector('.theme-toggle');
    const themeIcon = document.querySelector('.theme-icon');
    const languageSwitcher = document.querySelector('.language-switcher');
    const languageButton = document.querySelector('.language-button');
    const enrollModal = document.getElementById('enroll-modal');
    const enrollForm = enrollModal ? enrollModal.querySelector('form') : null;
    const enrollTitle = enrollModal ? enrollModal.querySelector('.modal-title') : null;
    const enrollCourseInput = enrollForm ? enrollForm.querySelector('input[name="course_id"]') : null;
    const enrollCloseButtons = enrollModal ? enrollModal.querySelectorAll('.modal-close') : [];
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    const setTheme = (mode) => {
        const theme = mode === 'dark' ? 'dark' : 'light';
        document.body.setAttribute('data-theme', theme);
        if (themeIcon) {
            themeIcon.textContent = theme === 'dark' ? themeIcon.dataset.dark : themeIcon.dataset.light;
        }
        localStorage.setItem('omk-theme', theme);
    };

    const savedTheme = localStorage.getItem('omk-theme');
    setTheme(savedTheme || (prefersDark ? 'dark' : 'light'));

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = document.body.getAttribute('data-theme');
            setTheme(current === 'dark' ? 'light' : 'dark');
        });
    }

    if (languageSwitcher && languageButton) {
        const toggleLanguageDropdown = (forceState) => {
            const isOpen = languageSwitcher.classList.contains('open');
            const nextState = typeof forceState === 'boolean' ? forceState : !isOpen;
            languageSwitcher.classList.toggle('open', nextState);
            languageButton.setAttribute('aria-expanded', String(nextState));
        };

        languageButton.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleLanguageDropdown();
        });

        languageSwitcher.querySelectorAll('.language-option').forEach(option => {
            option.addEventListener('click', () => toggleLanguageDropdown(false));
        });

        document.addEventListener('click', (event) => {
            if (!languageSwitcher.contains(event.target)) {
                toggleLanguageDropdown(false);
            }
        });
    }

    if (navToggle && navLinks) {
        navToggle.setAttribute('aria-expanded', 'false');
        const toggleNav = (forceState) => {
            const isOpen = typeof forceState === 'boolean'
                ? forceState
                : !navLinks.classList.contains('open');
            navLinks.classList.toggle('open', isOpen);
            document.body.classList.toggle('nav-open', isOpen);
            navToggle.setAttribute('aria-expanded', String(isOpen));
        };

        navToggle.addEventListener('click', () => toggleNav());

        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => toggleNav(false));
        });

        document.addEventListener('keyup', (event) => {
            if (event.key === 'Escape') {
                toggleNav(false);
            }
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth > 900) {
                toggleNav(false);
            }
        });
    }

    const openEnrollModal = (courseId, courseName) => {
        if (!enrollModal || !enrollForm || !enrollCourseInput || !enrollTitle) return;
        enrollCourseInput.value = courseId;
        const template = enrollTitle.dataset.titleTemplate || enrollTitle.textContent || '';
        enrollTitle.textContent = template.replace('{course}', courseName || '');
        enrollModal.classList.add('open');
        enrollModal.removeAttribute('hidden');
        const firstField = enrollForm.querySelector('input[name="full_name"]');
        if (firstField) {
            setTimeout(() => firstField.focus(), 50);
        }
        document.body.style.overflow = 'hidden';
    };

    const closeEnrollModal = () => {
        if (!enrollModal) return;
        enrollModal.classList.remove('open');
        enrollModal.setAttribute('hidden', '');
        document.body.style.overflow = '';
        enrollForm?.reset();
    };

    enrollCloseButtons.forEach(btn => btn.addEventListener('click', closeEnrollModal));

    if (enrollModal) {
        enrollModal.addEventListener('click', (event) => {
            if (event.target === enrollModal) {
                closeEnrollModal();
            }
        });
    }

    document.addEventListener('keyup', (event) => {
        if (event.key === 'Escape' && enrollModal && enrollModal.classList.contains('open')) {
            closeEnrollModal();
        }
    });

    document.querySelectorAll('.btn-enroll').forEach(button => {
        button.addEventListener('click', () => {
            const courseId = button.dataset.courseId;
            const courseName = button.dataset.courseName;
            openEnrollModal(courseId, courseName);
        });
    });

    document.querySelectorAll('.attendance-manager').forEach(manager => {
        const tabs = manager.querySelectorAll('.attendance-tab');
        const panels = manager.querySelectorAll('.attendance-table');
        if (!tabs.length) return;

        const activate = (targetId) => {
            tabs.forEach(tab => {
                tab.classList.toggle('active', tab.dataset.monthTarget === targetId);
            });
            panels.forEach(panel => {
                panel.classList.toggle('active', panel.dataset.monthPanel === targetId);
            });
        };

        tabs.forEach(tab => {
            tab.addEventListener('click', () => activate(tab.dataset.monthTarget));
        });
    });
});
