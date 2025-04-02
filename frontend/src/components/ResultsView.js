import React, { useState } from 'react';
import { Card, Table, Tab, Tabs, Accordion } from 'react-bootstrap';

const ResultsView = ({ results, extractedTerms, extractedText }) => {
  const [activeTab, setActiveTab] = useState('results');

  if (!results) return null;

  const getStatusClass = (status) => {
    switch (status) {
      case '✅': return 'status-valid';
      case '❌': return 'status-invalid';
      case '❓': return 'status-unknown';
      default: return '';
    }
  };

  return (
    <Card className="mb-4 results-container">
      <Card.Header as="h5">Validation Details</Card.Header>
      <Card.Body>
        <Tabs
          activeKey={activeTab}
          onSelect={(k) => setActiveTab(k)}
          className="mb-3"
        >
          <Tab eventKey="results" title="Validation Results">
            <div className="table-responsive results-table">
              <Table striped bordered hover>
                <thead>
                  <tr>
                    <th>Term</th>
                    <th>Extracted Value</th>
                    <th>Status</th>
                    <th>Expected Value</th>
                    <th>Allowed Range</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((row, index) => (
                    <tr key={index}>
                      <td>{row.Term}</td>
                      <td>{row['Extracted Value']}</td>
                      <td className={getStatusClass(row.Status)}>{row.Status}</td>
                      <td>{row['Expected Value']}</td>
                      <td>{row['Allowed Range']}</td>
                      <td>{row.Notes}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          </Tab>
          <Tab eventKey="extracted" title="Extracted Terms">
            <div className="mt-3">
              <h6>Structured Data Extracted from Term Sheet:</h6>
              <pre className="bg-light p-3 rounded">
                {JSON.stringify(extractedTerms, null, 2)}
              </pre>
            </div>
          </Tab>
          <Tab eventKey="rawtext" title="Extracted Text">
            <Accordion defaultActiveKey="0" className="mt-3">
              <Accordion.Item eventKey="0">
                <Accordion.Header>Term Sheet Text</Accordion.Header>
                <Accordion.Body>
                  <div className="extracted-text-container">
                    <pre>{extractedText}</pre>
                  </div>
                </Accordion.Body>
              </Accordion.Item>
            </Accordion>
          </Tab>
        </Tabs>
      </Card.Body>
    </Card>
  );
};

export default ResultsView;