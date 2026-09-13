/* ExamScope Interactive Radar JavaScript */

document.addEventListener('DOMContentLoaded', () => {
  const blips = document.querySelectorAll('.radar-blip');
  
  blips.forEach(blip => {
    blip.addEventListener('click', () => {
      const topicId = blip.getAttribute('data-topic-id');
      if (topicId) {
        openTopicDetailDrawer(topicId);
      }
    });
  });
});

async function openTopicDetailDrawer(topicId) {
  try {
    const res = await fetch(`/api/topic/${topicId}`);
    if (!res.ok) return;
    const data = await res.json();
    
    const topic = data.topic;
    const calc = data.calc;

    // Populate drawer elements
    document.getElementById('drawer-topic-name').textContent = topic.name;
    document.getElementById('drawer-risk-score').textContent = `${calc.risk_score}/100`;
    
    const badgeEl = document.getElementById('drawer-risk-badge');
    badgeEl.textContent = calc.risk_level;
    badgeEl.className = `badge-risk badge-risk-${calc.risk_level.toLowerCase()}`;

    document.getElementById('drawer-confidence').textContent = `${topic.confidence}%`;
    document.getElementById('drawer-practice').textContent = `${topic.practice_score}%`;
    document.getElementById('drawer-reviewed').textContent = calc.days_since_review === 0 ? 'Today' : `${calc.days_since_review}d ago`;

    document.getElementById('drawer-reason').textContent = calc.reason_summary;
    document.getElementById('drawer-action').textContent = calc.recommended_action;

    if (topic.notes) {
      document.getElementById('drawer-notes-container').classList.remove('hidden');
      document.getElementById('drawer-notes').textContent = topic.notes;
    } else {
      document.getElementById('drawer-notes-container').classList.add('hidden');
    }

    // Set form actions for inline actions
    const reviewForm = document.getElementById('drawer-review-form');
    if (reviewForm) reviewForm.action = `/topics/review/${topic.id}`;

    const editButton = document.getElementById('drawer-edit-btn');
    if (editButton) {
      editButton.onclick = () => {
        closeModal('topic-detail-drawer');
        openEditTopicModal(topic);
      };
    }

    openModal('topic-detail-drawer');
  } catch (err) {
    console.error('Failed to load topic details:', err);
  }
}

function openEditTopicModal(topic) {
  document.getElementById('edit-topic-form').action = `/topics/edit/${topic.id}`;
  document.getElementById('edit-topic-name').value = topic.name;
  document.getElementById('edit-topic-confidence').value = topic.confidence;
  document.getElementById('edit-confidence-val').textContent = `${topic.confidence}%`;
  document.getElementById('edit-topic-practice').value = topic.practice_score;
  document.getElementById('edit-practice-val').textContent = `${topic.practice_score}%`;
  document.getElementById('edit-topic-reviewed').value = topic.last_reviewed;
  document.getElementById('edit-topic-notes').value = topic.notes || '';
  
  openModal('edit-topic-modal');
}
