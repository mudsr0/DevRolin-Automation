import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Sidebar from '../components/Sidebar';
import KeywordBox from '../components/KeywordBox';
import { theme } from '../styles/theme';
import { getConfig } from '../api';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState(1);
  const [configParams, setConfigParams] = useState(null);

  useEffect(() => {
    const fetchConfig = async () => {
      const data = await getConfig();
      if (data) {
        setConfigParams(data);
      }
    };
    fetchConfig();
  }, []);

  const socialPlatforms = [
    {
      id: 'linkedin',
      title: 'LinkedIn',
      icon: 'https://cdn-icons-png.flaticon.com/512/174/174857.png',
      // gradient: `linear-gradient(135deg, #0077B5, #00A0DC)`,
      hasProfileInput: true,
      profileLabel: 'Person Profile URL',
      profilePlaceholder: 'https://linkedin.com/in/your-profile',
      keywordLabel: 'Search Keywords'
    },
    {
      id: 'twitter',
      title: 'X (Twitter)',
      icon: 'https://cdn-icons-png.flaticon.com/512/5968/5968830.png',
      gradient: `linear-gradient(135deg, #1DA1F2, #0C85D0)`,
      hasProfileInput: true,
      profileLabel: 'Username',
      profilePlaceholder: '@username',
      keywordLabel: 'Search Keywords'
    },
    {
      id: 'reddit',
      title: 'Reddit',
      icon: 'https://cdn-icons-png.flaticon.com/512/2111/2111589.png',
      // gradient: `linear-gradient(135deg, #FF4500, #FF5722)`,
      hasProfileInput: false,
      keywordLabel: 'Search Keywords'
    }
  ];

  return (
    <div className="flex min-h-screen" style={{ backgroundColor: theme.colors.background }}>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content */}
      <main className="flex-1 p-4 lg:p-8 overflow-y-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 mt-16 lg:mt-0"
        >
          <h1 className="text-3xl lg:text-4xl font-bold mb-2" style={{ color: theme.colors.text }}>
            Social Media Automation
          </h1>
          <p style={{ color: theme.colors.textSecondary }}>
            Manage your profiles and keywords across multiple platforms
          </p>
        </motion.div>

        {/* Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {socialPlatforms.map((platform, index) => {
            let initialProfiles = [];
            let initialKeywords = [];
            let backendKey = platform.id;
            
            if (configParams && configParams[backendKey]) {
              if (backendKey === 'reddit') {
                initialProfiles = []; // Reddit doesn't use subreddits in this UI component input directly
                initialKeywords = configParams[backendKey].keywords || [];
              } else if (backendKey === 'linkedin') {
                initialProfiles = configParams[backendKey].profiles || [];
                initialKeywords = configParams[backendKey].keywords || [];
              } else if (backendKey === 'twitter') {
                initialProfiles = configParams[backendKey].usernames || [];
                initialKeywords = configParams[backendKey].keywords || [];
              }
            }

            return (
              <motion.div
                key={platform.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <KeywordBox
                  id={platform.id}
                  title={platform.title}
                  icon={platform.icon}
                  gradient={platform.gradient}
                  hasProfileInput={platform.hasProfileInput}
                  profileLabel={platform.profileLabel}
                  profilePlaceholder={platform.profilePlaceholder}
                  keywordLabel={platform.keywordLabel}
                  initialProfiles={initialProfiles}
                  initialKeywords={initialKeywords}
                />
              </motion.div>
            );
          })}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;