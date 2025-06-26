import React, { useState } from 'react';
import { Container, Row, Col, Card, Spinner } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles/App.css';

// Import components
import FileUploader from './components/FileUploader';
import MasterSheetView from './components/MasterSheetView';
import ValidationSummary from './components/ValidationSummary';
import ResultsView from './components/ResultsView';

// Axios for API calls
import axios from 'axios';

function App() {
  const [termSheet, setTermSheet] = useState(null);
  const [masterSheet, setMasterSheet] = useState(null);
  const [loading, setLoading] = useState(false);
  const [validationResults, setValidationResults] = useState(null);
  const [masterSheetData, setMasterSheetData] = useState(null);
  const [extractedTerms, setExtractedTerms] = useState(null);
  const [summary, setSummary] = useState(null);
  const [extractedText, setExtractedText] = useState(null);
  const [reportUrls, setReportUrls] = useState({
    pdf: null,
    excel: null,
    html: null
  });

// Inside your handleValidate function:

const handleValidate = async () => {
    if (!termSheet || !masterSheet) {
      alert('Please upload both the term sheet and master sheet files.');
      return;
    }

    setLoading(true);

    try {
      // Create form data for file upload
      const formData = new FormData();
      formData.append('termsheet', termSheet);
      formData.append('mastersheet', masterSheet);

      // Use 127.0.0.1 explicitly instead of localhost
      const apiUrl = 'http://127.0.0.1:5000/api/validate';

      console.log('Sending request to:', apiUrl);
      
      const response = await axios.post(apiUrl, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Accept': 'application/json',
        }
      });

      console.log('Response received:', response.data);

      // Set state with response data
      setMasterSheetData(response.data.masterSheetData);
      setValidationResults(response.data.validationResults);
      setExtractedTerms(response.data.extractedTerms);
      setSummary(response.data.summary);
      setExtractedText(response.data.extractedText);
      
      // Update report URLs with the correct URL
      const baseReportUrl = 'http://127.0.0.1:5000/api/download/';
      
      setReportUrls({
        pdf: `${baseReportUrl}pdf`,
        excel: `${baseReportUrl}excel`,
        html: response.data.htmlReport
      });
    } catch (error) {
      console.error('Error details:', error);
      if (error.response) {
        // The server responded with a status code outside the 2xx range
        console.error('Server error data:', error.response.data);
        console.error('Server error status:', error.response.status);
        alert(`Server error ${error.response.status}: ${JSON.stringify(error.response.data)}`);
      } else if (error.request) {
        // The request was made but no response was received
        console.error('No response received. Is the server running?');
        alert('No response from server. Make sure the backend is running on port 5000.');
      } else {
        // Something happened in setting up the request
        alert(`Error: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
};

  return (
    <Container className="app-container">
      {loading && (
        <div className="loading-overlay">
          <div className="loading-content">
            <Spinner animation="border" role="status" />
            <p className="mt-3">Processing files. This may take a moment...</p>
          </div>
        </div>
      )}

      <div className="app-header">
        <h1>Term Sheet Validation Tool</h1>
        <p>Validate term sheets against a master sheet using OCR and NLP technology</p>
      </div>

      <Card className="mb-4">
        <Card.Header>How to use this tool</Card.Header>
        <Card.Body>
          <ol>
            <li>Upload a term sheet document (PDF, Word, Excel, or image)</li>
            <li>Upload a master sheet with expected terms and values (preferably Excel format)</li>
            <li>Click 'Validate Term Sheet' to process and validate the documents</li>
            <li>View the results and download reports in various formats</li>
          </ol>
          <p>The master sheet should contain columns for 'Term', 'Expected Value', and 'Allowed Range'.</p>
        </Card.Body>
      </Card>

      <Row className="mb-4">
        <Col md={6}>
          <FileUploader
            label="Term Sheet Upload"
            helpText="Upload the term sheet you want to validate"
            acceptedFiles={['.pdf', '.docx', '.xlsx', '.jpg', '.jpeg', '.png', '.tif', '.tiff']}
            onFileAccepted={(file) => setTermSheet(file)}
          />
        </Col>
        <Col md={6}>
          <FileUploader
            label="Master Sheet Upload"
            helpText="Upload the master sheet with expected values"
            acceptedFiles={['.xlsx', '.csv', '.pdf', '.docx']}
            onFileAccepted={(file) => setMasterSheet(file)}
          />
        </Col>
      </Row>

      <div className="d-grid gap-2 col-6 mx-auto mb-4">
        <button 
          className="btn btn-primary btn-lg" 
          onClick={handleValidate}
          disabled={!termSheet || !masterSheet || loading}
        >
          {loading ? (
            <>
              <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
              <span className="ms-2">Validating...</span>
            </>
          ) : (
            'Validate Term Sheet'
          )}
        </button>
      </div>

      {masterSheetData && (
        <MasterSheetView data={masterSheetData} />
      )}

      {validationResults && summary && (
        <>
          <ValidationSummary 
            summary={summary} 
            reportUrls={reportUrls}
          />
          <ResultsView 
            results={validationResults} 
            extractedTerms={extractedTerms}
            extractedText={extractedText}
          />
        </>
      )}
    </Container>
  );
}

export default App;