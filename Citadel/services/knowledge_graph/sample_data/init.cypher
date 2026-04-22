// Sample initial graph for demonstration
CREATE (b:Building {name: 'HQ'});
CREATE (s1:Sensor {id: 'sensor1', type: 'temperature'});
CREATE (s2:Sensor {id: 'sensor2', type: 'humidity'});
CREATE (s1)-[:INSTALLED_IN]->(b);
CREATE (s2)-[:INSTALLED_IN]->(b);