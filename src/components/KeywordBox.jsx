import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiX, FiPlus, FiCheck } from 'react-icons/fi';
import { theme } from '../styles/theme';
import { updatePlatformConfig } from '../api';

const KeywordBox = ({
  id,
  title,
  icon,
  gradient,
  hasProfileInput = false,
  profileLabel = '',
  profilePlaceholder = '',
  keywordLabel = 'Search Keywords',
  initialProfiles = [],
  initialKeywords = []
}) => {
  // Profile Management
  const [profileInput, setProfileInput] = useState('');
  const [profiles, setProfiles] = useState(initialProfiles);
  const [profileError, setProfileError] = useState('');
  
  // Keywords Management
  const [keywords, setKeywords] = useState(initialKeywords);
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null); // null, 'success', 'error'

  useEffect(() => {
    setProfiles(initialProfiles);
  }, [initialProfiles]);

  useEffect(() => {
    setKeywords(initialKeywords);
  }, [initialKeywords]);

  // Validate Profile URL/Username
  const validateProfile = (url) => {
    if (!url.trim()) {
      setProfileError('Profile URL/Username cannot be empty');
      return false;
    }
    
    if (id === 'twitter' && !url.startsWith('@')) {
      setProfileError('Twitter username should start with @');
      return false;
    }
    
    if (id === 'linkedin' && !url.includes('linkedin.com')) {
      setProfileError('Please enter a valid LinkedIn URL');
      return false;
    }

    if (profiles.includes(url.trim())) {
      setProfileError('This profile already exists');
      return false;
    }
    
    setProfileError('');
    return true;
  };

  // Add Profile
  const handleAddProfile = () => {
    if (validateProfile(profileInput)) {
      setProfiles([...profiles, profileInput.trim()]);
      setProfileInput('');
    }
  };

  const handleProfileKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddProfile();
    }
  };

  const removeProfile = (indexToRemove) => {
    setProfiles(profiles.filter((_, index) => index !== indexToRemove));
  };

  const clearAllProfiles = () => {
    setProfiles([]);
  };

  // Add Keyword
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault();
      if (!keywords.includes(inputValue.trim())) {
        setKeywords([...keywords, inputValue.trim()]);
      }
      setInputValue('');
    }
  };

  const removeKeyword = (indexToRemove) => {
    setKeywords(keywords.filter((_, index) => index !== indexToRemove));
  };

  const clearAllKeywords = () => {
    setKeywords([]);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl p-6 h-full flex flex-col"
      style={{
        backgroundColor: theme.colors.surface,
        border: `1px solid ${theme.colors.border}`
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <div 
          className="w-16 h-16 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: gradient }}
        >
          <img src={icon} alt={title} className="w-8 h-8 object-contain" />
        </div>
        <h3 className="text-xl font-bold" style={{ color: theme.colors.text }}>
          {title}
        </h3>
      </div>

      {/* Profile Input Section */}
      {hasProfileInput && (
        <div className="mb-6 pb-6" style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
          <label className="block text-sm font-medium mb-3" style={{ color: theme.colors.text }}>
            {profileLabel} <span style={{ color: theme.colors.textSecondary }}>
              (Optional)
            </span>
          </label>

          {/* Profile Input Field */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-2"
          >
            <div className="relative">
              <input
                type="text"
                value={profileInput}
                onChange={(e) => {
                  setProfileInput(e.target.value);
                  setProfileError('');
                }}
                onKeyPress={handleProfileKeyPress}
                placeholder={profilePlaceholder}
                className="w-full px-4 py-3 rounded-lg outline-none transition-all"
                style={{
                  backgroundColor: theme.colors.secondaryLight,
                  border: `2px solid ${profileError ? theme.colors.error : theme.colors.border}`,
                  color: theme.colors.text
                }}
                onFocus={(e) => {
                  if (!profileError) {
                    e.target.style.borderColor = theme.colors.primary;
                  }
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = profileError ? theme.colors.error : theme.colors.border;
                }}
              />
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleAddProfile}
                className="absolute right-3 top-1/2 -translate-y-1/2 transition-all"
                style={{ color: theme.colors.primary }}
              >
                <FiPlus size={20} />
              </motion.button>
            </div>

            {/* Error Message */}
            <AnimatePresence>
              {profileError && (
                <motion.p
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="text-xs font-medium"
                  style={{ color: theme.colors.error }}
                >
                  {profileError}
                </motion.p>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Profiles Display */}
          {profiles.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4"
            >
              <div className="flex flex-wrap gap-2 mb-3">
                <AnimatePresence>
                  {profiles.map((profile, index) => (
                    <motion.span
                      key={index}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      className="px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium"
                      style={{
                        backgroundColor: theme.colors.secondaryLight,
                        color: theme.colors.text,
                        border: `1px solid ${theme.colors.primary}`
                      }}
                    >
                      <span className="text-green-400">✓</span>
                      <span className="truncate">{profile}</span>
                      <button
                        onClick={() => removeProfile(index)}
                        className="hover:opacity-70 transition-opacity ml-1"
                        style={{ color: theme.colors.primary }}
                      >
                        <FiX size={16} />
                      </button>
                    </motion.span>
                  ))}
                </AnimatePresence>
              </div>

              {/* Clear All Profiles Button - Shows when > 2 profiles */}
              {profiles.length > 2 && (
                <motion.button
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={clearAllProfiles}
                  className="w-full py-2 rounded-lg text-sm font-medium transition-all"
                  style={{
                    backgroundColor: theme.colors.secondaryLight,
                    color: theme.colors.error,
                    border: `1px solid ${theme.colors.border}`
                  }}
                >
                  Clear All Profiles
                </motion.button>
              )}
            </motion.div>
          )}
        </div>
      )}

      {/* Keywords Section */}
      <div className="flex-1 flex flex-col">
        <label className="block text-sm font-medium mb-3" style={{ color: theme.colors.text }}>
          {keywordLabel} <span style={{ color: theme.colors.textSecondary }}>
            (Optional)
          </span>
        </label>

        {/* Keyword Input */}
        <div className="mb-4">
          <div className="relative">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type keyword and press Enter"
              className="w-full px-4 py-3 rounded-lg outline-none transition-all"
              style={{
                backgroundColor: theme.colors.secondaryLight,
                border: `2px solid ${theme.colors.border}`,
                color: theme.colors.text
              }}
              onFocus={(e) => e.target.style.borderColor = theme.colors.primary}
              onBlur={(e) => e.target.style.borderColor = theme.colors.border}
            />
            <FiPlus 
              className="absolute right-4 top-1/2 -translate-y-1/2"
              style={{ color: theme.colors.textSecondary }}
            />
          </div>
        </div>

        {/* Keywords Display */}
        <div className="flex-1 overflow-y-auto">
          <AnimatePresence>
            {keywords.length > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col gap-3"
              >
                <div className="flex flex-wrap gap-2">
                  {keywords.map((keyword, index) => (
                    <motion.span
                      key={index}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      className="px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium"
                      style={{
                        backgroundColor: theme.colors.secondaryLight,
                        color: theme.colors.text,
                        border: `1px solid ${theme.colors.border}`
                      }}
                    >
                      {keyword}
                      <button
                        onClick={() => removeKeyword(index)}
                        className="hover:opacity-70 transition-opacity"
                        style={{ color: theme.colors.primary }}
                      >
                        <FiX size={16} />
                      </button>
                    </motion.span>
                  ))}
                </div>

                {/* Clear All Keywords Button - Shows when > 2 keywords */}
                {keywords.length > 2 && (
                  <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={clearAllKeywords}
                    className="w-full py-2 rounded-lg text-sm font-medium transition-all"
                    style={{
                      backgroundColor: theme.colors.secondaryLight,
                      color: theme.colors.error,
                      border: `1px solid ${theme.colors.border}`
                    }}
                  >
                    Clear All Keywords
                  </motion.button>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {keywords.length === 0 && (
            <div 
              className="text-center py-8"
              style={{ color: theme.colors.textSecondary }}
            >
              No keywords added yet
            </div>
          )}
        </div>
      </div>

      {/* Submit Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={async () => {
          setIsSubmitting(true);
          setSubmitStatus(null);
          try {
            let payload = { keywords };
            if (id === 'reddit') {
              payload.subreddits = [];
            } else if (id === 'linkedin') {
              payload.profiles = profiles;
            } else if (id === 'twitter') {
              payload.usernames = profiles;
            }
            
            await updatePlatformConfig(id, payload);
            setSubmitStatus('success');
            setTimeout(() => setSubmitStatus(null), 3000); // clear status after 3s
          } catch (error) {
            console.error(error);
            setSubmitStatus('error');
          } finally {
            setIsSubmitting(false);
          }
        }}
        disabled={isSubmitting}
        className="w-full py-3 rounded-lg font-medium transition-all mt-4"
        style={{
          backgroundColor: submitStatus === 'success' ? '#10B981' : submitStatus === 'error' ? theme.colors.error : theme.colors.primary,
          color: theme.colors.text,
          opacity: isSubmitting ? 0.7 : 1
        }}
      >
        {isSubmitting ? 'Submitting...' : submitStatus === 'success' ? 'Saved Successfully!' : submitStatus === 'error' ? 'Error Saving' : 'Submit'}
      </motion.button>
      
    </motion.div>
  );
};

export default KeywordBox;