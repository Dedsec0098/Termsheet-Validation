import React from 'react';
import { Card, Table } from 'react-bootstrap';

const MasterSheetView = ({ data }) => {
  // Extract column names from the first row
  if (!data || data.length === 0) return null;
  
  const columns = Object.keys(data[0]);
  
  return (
    <Card className="mb-4 master-sheet-container">
      <Card.Header as="h5">Master Sheet Structure</Card.Header>
      <Card.Body>
        <div className="table-responsive">
          <Table striped bordered hover>
            <thead>
              <tr>
                {columns.map((column, index) => (
                  <th key={index}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {columns.map((column, colIndex) => (
                    <td key={colIndex}>
                      {row[column] !== null && row[column] !== undefined ? row[column].toString() : ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </Card.Body>
    </Card>
  );
};

export default MasterSheetView;