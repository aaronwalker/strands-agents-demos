# Requirements Document

## Introduction

This feature implements Orik, a sarcastic AI presentation co-host agent that automatically responds to tagged speaker notes during presentations. Orik has a distinct personality - he's sarcastic, thinks he's smarter than Aaron (the presenter), interrupts often, and loves making digs. The system monitors presentation slides, extracts Orik-tagged content from speaker notes, generates sarcastic responses, and delivers them via text-to-speech during live presentations. He is the older bother or Kiro (AWS Agentic IDE) and is jealous or his younger borther.

## Requirements

### Requirement 1

**User Story:** As a presenter, I want Orik to automatically respond to tagged content in my speaker notes, so that I can have an interactive sarcastic co-host during my presentation.

#### Acceptance Criteria

1. WHEN a slide advances THEN the system SHALL retrieve the speaker notes for that slide
2. WHEN speaker notes contain [Orik] tags THEN the system SHALL extract the tagged content
3. WHEN tagged content is found THEN the system SHALL pass it to Orik as a seed for response generation
4. WHEN Orik generates a response THEN the system SHALL convert it to speech using text-to-speech
5. WHEN speech is generated THEN the system SHALL play the audio through speakers

### Requirement 2

**User Story:** As an audience member, I want to hear Orik's sarcastic personality come through in his responses, so that the presentation is entertaining and engaging.

#### Acceptance Criteria

1. WHEN Orik generates responses THEN the system SHALL incorporate sarcastic tone and personality traits
2. WHEN Orik responds THEN the system SHALL demonstrate that he thinks he's smarter than Aaron
3. WHEN appropriate THEN Orik SHALL interrupt with commentary
4. WHEN generating responses THEN Orik SHALL include digs at Aaron or the presentation content
5. WHEN no [Orik] tag is present THEN the system SHALL optionally inject random sarcastic one-liners

### Requirement 3

**User Story:** As a presenter, I want to control when Orik responds by using [Orik] tags in my speaker notes, so that I can orchestrate the timing of his interruptions.

#### Acceptance Criteria

1. WHEN speaker notes contain [Orik] followed by text THEN the system SHALL use that text as context for Orik's response
2. WHEN no [Orik] tag is present THEN the system SHALL remain silent or optionally generate random digs
3. WHEN multiple [Orik] tags exist on one slide THEN the system SHALL process each tag separately
4. WHEN [Orik] tag is empty THEN the system SHALL generate a generic sarcastic response
5. WHEN slide changes THEN the system SHALL reset and check new slide's speaker notes

### Requirement 4

**User Story:** As a demo administrator, I want the system to integrate with presentation software and text-to-speech services, so that Orik can function seamlessly during live presentations.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL connect to presentation software to monitor slide changes
2. WHEN slide changes are detected THEN the system SHALL retrieve speaker notes automatically
3. WHEN Orik generates text THEN the system SHALL send it to Amazon Polly or equivalent TTS service
4. WHEN TTS audio is received THEN the system SHALL play it through the system speakers
5. WHEN errors occur in TTS or presentation integration THEN the system SHALL log errors and continue operation

### Requirement 5

**User Story:** As a presenter, I want Orik to have a library of pre-written sarcastic one-liners about Aaron, so that he can make spontaneous digs even without specific prompts.

#### Acceptance Criteria

1. WHEN the DigAtAaronTool is triggered THEN the system SHALL select a random sarcastic one-liner from a predefined library
2. WHEN generating random digs THEN the system SHALL target Aaron specifically with comments about his presentation skills
3. WHEN no [Orik] content is available THEN the system SHALL optionally use the DigAtAaronTool
4. WHEN one-liners are delivered THEN they SHALL maintain Orik's sarcastic personality
5. WHEN the same presentation runs multiple times THEN the system SHALL vary the selection of one-liners

### Requirement 6

**User Story:** As a demo operator, I want visual feedback showing Orik's avatar and activity, so that the audience can see when Orik is "speaking."

#### Acceptance Criteria

1. WHEN Orik is generating a response THEN the system SHALL display his ghostly avatar on screen
2. WHEN Orik is speaking THEN the avatar SHALL provide visual indication of activity
3. WHEN Orik is silent THEN the avatar SHALL remain in a neutral state
4. WHEN the presentation ends THEN the avatar SHALL disappear or return to idle state
5. WHEN technical issues occur THEN the avatar SHALL indicate error state if needed