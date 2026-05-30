from flask import Flask, request, jsonify

from templates.meeting_data import summarize_meeting, extract_meeting_takeaways, extract_case_studies, \
    extract_article_suggestions, write_email

app = Flask(__name__)


@app.route('/process_meeting', methods=['POST'])
def process_meeting():
    try:
        # Parse JSON input
        data = request.get_json()
        if not data or 'meeting_transcript' not in data:
            return jsonify({"error": "Invalid input, 'meeting_transcript' is required"}), 400

        meeting_transcript = data['meeting_transcript']

        # Process meeting
        meeting_summary = summarize_meeting(meeting_transcript)
        meeting_takeaways = extract_meeting_takeaways(meeting_summary)
        case_studies = extract_case_studies(meeting_summary)
        article_suggestions = extract_article_suggestions(meeting_summary)

        # Generate email template
        email = write_email(meeting_takeaways, article_suggestions, case_studies)

        # Return the response as JSON
        return jsonify({
            "email_title": email.title,
            "email_message": email.message
        })
    except Exception as e:
        # Handle exceptions gracefully
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)