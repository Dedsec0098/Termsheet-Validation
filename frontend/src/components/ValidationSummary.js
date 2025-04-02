import React from 'react';
import { Card, Button, Row, Col } from 'react-bootstrap';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

const ValidationSummary = ({ summary, reportUrls }) => {
  if (!summary) return null;

  // Data for pie chart
  const chartData = {
    labels: ['Valid', 'Invalid', 'Unknown'],
    datasets: [
      {
        data: [
          summary.validTerms,
          summary.invalidTerms,
          summary.unknownTerms
        ],
        backgroundColor: [
          '#4CAF50',  // green
          '#F44336',  // red
          '#FFC107'   // amber
        ],
        borderWidth: 1,
      },
    ],
  };

  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  };

  const handleDownloadReport = (type) => {
    if (reportUrls[type]) {
      window.open(reportUrls[type], '_blank');
    }
  };

  return (
    <Card className="mb-4">
      <Card.Header as="h5">Validation Summary</Card.Header>
      <Card.Body>
        <Row>
          <Col md={6}>
            <div className="summary-stats">
              <div className="summary-stat-item total-terms">
                <h3>{summary.totalTerms}</h3>
                <p>Total Terms</p>
              </div>
              <div className="summary-stat-item valid-terms">
                <h3>{summary.validTerms}</h3>
                <p>Valid Terms ({summary.validPercent.toFixed(1)}%)</p>
              </div>
              <div className="summary-stat-item invalid-terms">
                <h3>{summary.invalidTerms}</h3>
                <p>Invalid Terms ({summary.invalidPercent.toFixed(1)}%)</p>
              </div>
            </div>
          </Col>
          <Col md={6}>
            <div className="chart-container" style={{ height: '250px' }}>
              <Pie data={chartData} options={chartOptions} />
            </div>
          </Col>
        </Row>

        <div className="download-buttons">
          <Button 
            variant="primary" 
            className="download-btn"
            onClick={() => handleDownloadReport('pdf')}
          >
            Download PDF Report
          </Button>
          <Button 
            variant="success" 
            className="download-btn"
            onClick={() => handleDownloadReport('excel')}
          >
            Download Excel Report
          </Button>
        </div>
      </Card.Body>
    </Card>
  );
};

export default ValidationSummary;