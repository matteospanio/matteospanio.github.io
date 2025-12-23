// get the ninja-keys element
const ninja = document.querySelector('ninja-keys');

// add the home and posts menu items
ninja.data = [{
    id: "nav-about",
    title: "about",
    section: "Navigation",
    handler: () => {
      window.location.href = "/";
    },
  },{id: "nav-blog",
          title: "blog",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/blog/";
          },
        },{id: "nav-publications",
          title: "publications",
          description: "Here is a list of my publications in reverse chronological order.",
          section: "Navigation",
          handler: () => {
            window.location.href = "/publications/";
          },
        },{id: "nav-projects",
          title: "projects",
          description: "A collection of my cool projects.",
          section: "Navigation",
          handler: () => {
            window.location.href = "/projects/";
          },
        },{id: "nav-repositories",
          title: "repositories",
          description: "Here is a list of links to my github main projects.",
          section: "Navigation",
          handler: () => {
            window.location.href = "/repositories/";
          },
        },{id: "nav-cv",
          title: "cv",
          description: "A brief summary of my academic and professional career. Click on the PDF icon to download a copy of my CV.",
          section: "Navigation",
          handler: () => {
            window.location.href = "/cv/";
          },
        },{id: "nav-teaching",
          title: "teaching",
          description: "Here are the materials used to support my teaching activity.",
          section: "Navigation",
          handler: () => {
            window.location.href = "/teaching/";
          },
        },{id: "post-making-scientific-python-blazingly-fast-with-pytorch",
        
          title: "Making scientific python blazingly fast with PyTorch",
        
        description: "A deep dive into using PyTorch for high-performance scientific computing",
        section: "Posts",
        handler: () => {
          
            window.location.href = "/blog/2025/slow-python/";
          
        },
      },{id: "post-python-39-s-virtual-environments",
        
          title: "Python&#39;s virtual environments",
        
        description: "A brief introduction to Python&#39;s virtual environments.",
        section: "Posts",
        handler: () => {
          
            window.location.href = "/blog/2024/python-environments/";
          
        },
      },{id: "post-python-39-s-static-typing-safari-in-search-of-code-clarity",
        
          title: "Python&#39;s Static Typing Safari: In Search of Code Clarity",
        
        description: "A brief introduction to Python&#39;s static typing and its benefits.",
        section: "Posts",
        handler: () => {
          
            window.location.href = "/blog/2023/python-static-typing/";
          
        },
      },{id: "post-principles-of-statistic",
        
          title: "Principles of statistic",
        
        description: "An introduction to statistic",
        section: "Posts",
        handler: () => {
          
            window.location.href = "/blog/2022/Principles-of-statistic/";
          
        },
      },{id: "post-dsp-il-suono-in-digitale",
        
          title: "DSP: il suono in digitale",
        
        description: "",
        section: "Posts",
        handler: () => {
          
            window.location.href = "/blog/2021/DSP-il-suono-in-digitale/";
          
        },
      },{id: "books-the-godfather",
          title: 'The Godfather',
          description: "",
          section: "Books",handler: () => {
              window.location.href = "/books/the_godfather/";
            },},{id: "news-today-dr-alessandro-russo-is-presenting-our-new-article-enhancing-preservation-and-restoration-of-open-reel-audio-tapes-through-computer-vision-at-the-international-conference-of-image-analysis-and-processing-iciap-2023-in-udine-see-you-there",
          title: 'Today Dr. Alessandro Russo is presenting our new article “Enhancing Preservation and Restoration...',
          description: "",
          section: "News",},{id: "news-i-will-attend-the-7th-advanced-course-on-data-science-amp-amp-machine-learning-acdl-from-10-to-14-june-see-you-there",
          title: 'I will attend the 7th Advanced Course on Data Science &amp;amp;amp; Machine Learning...',
          description: "",
          section: "News",},{id: "news-a-new-paper-titled-a-novel-derivative-based-approach-for-the-automatic-detection-of-time-reversed-audio-in-the-mpai-ieee-cae-arp-international-standard-by-marina-bosi-fabio-zanini-alessandro-russo-sergio-canazza-and-me-has-been-accepted-at-the-aes-show-2024-that-will-take-place-in-new-york-from-8-to-10-october-2024-see-you-in-new-york",
          title: 'A new paper titled A novel derivative-based approach for the automatic detection of...',
          description: "",
          section: "News",},{id: "news-my-two-new-papers-towards-emotionally-aware-ai-challenges-and-opportunities-in-the-evolution-of-multimodal-generative-models-and-filming-the-sound-anomaly-detection-on-audio-tape-recordings-using-computer-vision-algorithms-have-been-accepted-for-publication-at-the-23rd-international-conference-of-the-italian-association-for-artificial-intelligence-that-will-take-place-in-bozen-between-25-and-28-november-see-you-there",
          title: 'My two new papers Towards Emotionally Aware AI: Challenges and Opportunities in the...',
          description: "",
          section: "News",},{id: "news-i-am-happy-to-announce-the-release-of-a-our-new-deep-learning-model-for-synesthetic-music-generation-it-is-available-for-download-on-hugging-face-learn-more-about-it-in-our-preprint-paper-enjoy",
          title: 'I am happy to announce the release of a our new deep learning...',
          description: "",
          section: "News",},{id: "news-next-week-i-ll-present-torchfx-a-new-python-library-for-gpu-accelerated-audio-effects-at-dafx-2025-in-ancona-italy-the-conference-will-take-place-from-2-to-6-september-2025-hope-to-see-you-there",
          title: 'Next week I’ll present torchfx, a new python library for GPU accelerated audio...',
          description: "",
          section: "News",},{id: "projects-spam-analyzer",
          title: 'spam-analyzer',
          description: "an AI enhanced companion to find spam emails",
          section: "Projects",handler: () => {
              window.location.href = "/projects/3_project/";
            },},{id: "projects-ml-project-template",
          title: 'ML Project template',
          description: "a template to train ML/DL models on a SLURM cluster",
          section: "Projects",handler: () => {
              window.location.href = "/projects/4_project/";
            },},{id: "teaching-dati-e-algoritmi",
          title: 'Dati e Algoritmi',
          description: "laboratorio di programmazione C per il corso di Dati e Algoritmi di Ingegneria Elettronica all&#39;Università di Padova",
          section: "Teaching",handler: () => {
              window.location.href = "/teaching/dati_e_algoritmi/";
            },},{
        id: 'social-academia_edu',
        title: 'Academia_edu',
        section: 'Socials',
        handler: () => {
          window.open("", "_blank");
        },
      },{
        id: 'social-email',
        title: 'email',
        section: 'Socials',
        handler: () => {
          window.open("mailto:%73%70%61%6E%69%6F@%64%65%69.%75%6E%69%70%64.%69%74", "_blank");
        },
      },{
        id: 'social-github',
        title: 'GitHub',
        section: 'Socials',
        handler: () => {
          window.open("https://github.com/matteospanio", "_blank");
        },
      },{
        id: 'social-gitlab',
        title: 'GitLab',
        section: 'Socials',
        handler: () => {
          window.open("https://gitlab.com/matteospanio", "_blank");
        },
      },{
        id: 'social-ieee',
        title: 'IEEE Xplore',
        section: 'Socials',
        handler: () => {
          window.open("https://ieeexplore.ieee.org/author/535146737522986/", "_blank");
        },
      },{
        id: 'social-kaggle',
        title: 'Kaggle',
        section: 'Socials',
        handler: () => {
          window.open("https://www.kaggle.com/gigioaquilani", "_blank");
        },
      },{
        id: 'social-linkedin',
        title: 'LinkedIn',
        section: 'Socials',
        handler: () => {
          window.open("https://www.linkedin.com/in/matteo-spanio", "_blank");
        },
      },{
        id: 'social-orcid',
        title: 'ORCID',
        section: 'Socials',
        handler: () => {
          window.open("https://orcid.org/0000-0002-2436-7208", "_blank");
        },
      },{
        id: 'social-researchgate',
        title: 'ResearchGate',
        section: 'Socials',
        handler: () => {
          window.open("https://www.researchgate.net/profile/Matteo-Spanio/", "_blank");
        },
      },{
        id: 'social-rss',
        title: 'RSS Feed',
        section: 'Socials',
        handler: () => {
          window.open("/feed.xml", "_blank");
        },
      },{
        id: 'social-scholar',
        title: 'Google Scholar',
        section: 'Socials',
        handler: () => {
          window.open("https://scholar.google.com/citations?user=CEWwcjUAAAAJ", "_blank");
        },
      },{
        id: 'social-scopus',
        title: 'Scopus',
        section: 'Socials',
        handler: () => {
          window.open("https://www.scopus.com/authid/detail.uri?authorId=58864999500", "_blank");
        },
      },{
      id: 'light-theme',
      title: 'Change theme to light',
      description: 'Change the theme of the site to Light',
      section: 'Theme',
      handler: () => {
        setThemeSetting("light");
      },
    },
    {
      id: 'dark-theme',
      title: 'Change theme to dark',
      description: 'Change the theme of the site to Dark',
      section: 'Theme',
      handler: () => {
        setThemeSetting("dark");
      },
    },
    {
      id: 'system-theme',
      title: 'Use system default theme',
      description: 'Change the theme of the site to System Default',
      section: 'Theme',
      handler: () => {
        setThemeSetting("system");
      },
    },];
