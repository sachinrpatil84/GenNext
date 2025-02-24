// Main Spring Boot Application
package com.trading.impactassessment;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.mongodb.repository.config.EnableMongoRepositories;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableMongoRepositories
@EnableScheduling
public class TradingImpactAssessmentApplication {
    public static void main(String[] args) {
        SpringApplication.run(TradingImpactAssessmentApplication.class, args);
    }
}

// Domain Models
package com.trading.impactassessment.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.util.List;
import java.util.Date;

@Document(collection = "workflows")
public class Workflow {
    @Id
    private String id;
    private String name;
    private String description;
    private String workflowType; // e.g. "Equities Cash"
    private List<String> impactedSystems;
    private Date lastUpdated;
    
    // Getters and setters
}

@Document(collection = "systems")
public class System {
    @Id
    private String id;
    private String name;
    private String description;
    private List<Component> components;
    private List<String> dependencies;
    private String gitProjectUrl;
    
    // Getters and setters
}

@Document(collection = "components")
public class Component {
    @Id
    private String id;
    private String name;
    private String description;
    private List<String> classNames;
    private String systemId;
    private String applicationStack;
    
    // Getters and setters
}

@Document(collection = "regulations")
public class Regulation {
    @Id
    private String id;
    private String name;
    private String description;
    private Date effectiveDate;
    private List<String> relatedDocuments;
    
    // Getters and setters
}

@Document(collection = "impactAssessments")
public class ImpactAssessment {
    @Id
    private String id;
    private String workflowId;
    private String regulationId;
    private Date creationDate;
    private String status;
    private List<SystemImpact> impactedSystems;
    private List<String> generatedRequirements;
    private double automationConfidence;
    
    // Getters and setters
}

public class SystemImpact {
    private String systemId;
    private String systemName;
    private String impactLevel; // HIGH, MEDIUM, LOW
    private List<String> impactedClasses;
    private List<String> testCases;
    private String jiraTicketId;
    
    // Getters and setters
}

// MongoDB Repositories
package com.trading.impactassessment.repository;

import com.trading.impactassessment.model.Workflow;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface WorkflowRepository extends MongoRepository<Workflow, String> {
    List<Workflow> findByWorkflowType(String workflowType);
}

@Repository
public interface SystemRepository extends MongoRepository<System, String> {
    List<System> findByNameIn(List<String> systemNames);
}

@Repository
public interface ComponentRepository extends MongoRepository<Component, String> {
    List<Component> findBySystemId(String systemId);
}

@Repository
public interface RegulationRepository extends MongoRepository<Regulation, String> {
}

@Repository
public interface ImpactAssessmentRepository extends MongoRepository<ImpactAssessment, String> {
    List<ImpactAssessment> findByWorkflowId(String workflowId);
    List<ImpactAssessment> findByRegulationId(String regulationId);
}

// Data Ingestion Services
package com.trading.impactassessment.service.ingestion;

import com.trading.impactassessment.model.Workflow;
import com.trading.impactassessment.repository.WorkflowRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class ConfluenceConnector {
    private final String CONFLUENCE_API_URL = "https://your-confluence-instance/rest/api";
    private final String API_TOKEN = "your-api-token";
    
    @Autowired
    private WorkflowRepository workflowRepository;
    
    public List<String> fetchDocumentationByWorkflow(String workflowType) {
        // Implement API call to confluence to get documentation
        // Parse documentation and return content
        return null;
    }
    
    public void synchronizeWorkflows() {
        // Logic to sync workflow documentation from Confluence
    }
}

@Service
public class JiraConnector {
    private final String JIRA_API_URL = "https://your-jira-instance/rest/api/2";
    private final String API_TOKEN = "your-api-token";
    
    public List<String> fetchJiraTicketsForSystem(String systemName) {
        // Implement API call to JIRA to get tickets for a system
        return null;
    }
    
    public void createJiraTicket(String systemName, String description, String impact) {
        // Logic to create a JIRA ticket for an impacted system
    }
}

@Service
public class GitConnector {
    
    public List<String> findClassesInRepository(String gitUrl, String path) {
        // Connect to Git repo and find classes in the specified path
        return null;
    }
    
    public List<String> findDependenciesBetweenClasses(String gitUrl, List<String> classNames) {
        // Analyze code to find dependencies between classes
        return null;
    }
}

// Analysis Services
package com.trading.impactassessment.service.analysis;

import com.trading.impactassessment.model.*;
import com.trading.impactassessment.repository.*;
import com.trading.impactassessment.service.ingestion.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.*;

@Service
public class WorkflowAnalysisService {
    
    @Autowired
    private WorkflowRepository workflowRepository;
    
    @Autowired
    private SystemRepository systemRepository;
    
    @Autowired
    private ConfluenceConnector confluenceConnector;
    
    public Map<String, Object> analyzeWorkflow(String workflowId) {
        Optional<Workflow> workflow = workflowRepository.findById(workflowId);
        if (workflow.isPresent()) {
            List<String> impactedSystems = workflow.get().getImpactedSystems();
            List<System> systems = systemRepository.findByNameIn(impactedSystems);
            
            // Get documentation
            List<String> documentation = confluenceConnector.fetchDocumentationByWorkflow(workflow.get().getWorkflowType());
            
            // Perform analysis
            Map<String, Object> analysis = new HashMap<>();
            analysis.put("workflow", workflow.get());
            analysis.put("systems", systems);
            analysis.put("documentation", documentation);
            
            return analysis;
        }
        return null;
    }
}

@Service
public class CodeImpactAnalysisService {
    
    @Autowired
    private GitConnector gitConnector;
    
    @Autowired
    private ComponentRepository componentRepository;
    
    public List<String> identifyImpactedClasses(String systemId, String changeDescription) {
        List<Component> components = componentRepository.findBySystemId(systemId);
        List<String> impactedClasses = new ArrayList<>();
        
        for (Component component : components) {
            // Use NLP to determine if component is likely impacted by the change description
            boolean isImpacted = analyzeComponentImpact(component, changeDescription);
            
            if (isImpacted) {
                // Add component's classes to impacted list
                impactedClasses.addAll(component.getClassNames());
            }
        }
        
        return impactedClasses;
    }
    
    private boolean analyzeComponentImpact(Component component, String changeDescription) {
        // Implement NLP logic to determine if a component is impacted
        // This would use historical patterns and keyword matching
        return false;
    }
}

@Service
public class TestCaseGenerationService {
    
    public List<String> generateTestCases(List<String> impactedClasses, String systemId) {
        List<String> testCases = new ArrayList<>();
        
        // For each impacted class, generate appropriate test cases
        for (String className : impactedClasses) {
            List<String> classCases = generateTestsForClass(className, systemId);
            testCases.addAll(classCases);
        }
        
        return testCases;
    }
    
    private List<String> generateTestsForClass(String className, String systemId) {
        // Generate test cases specific to the class based on its functionality
        // This would use templates and historical test patterns
        return new ArrayList<>();
    }
}

// Impact Assessment Service
package com.trading.impactassessment.service;

import com.trading.impactassessment.model.*;
import com.trading.impactassessment.repository.*;
import com.trading.impactassessment.service.analysis.*;
import com.trading.impactassessment.service.ingestion.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.*;

@Service
public class ImpactAssessmentService {
    
    @Autowired
    private WorkflowRepository workflowRepository;
    
    @Autowired
    private SystemRepository systemRepository;
    
    @Autowired
    private ImpactAssessmentRepository impactAssessmentRepository;
    
    @Autowired
    private WorkflowAnalysisService workflowAnalysisService;
    
    @Autowired
    private CodeImpactAnalysisService codeImpactAnalysisService;
    
    @Autowired
    private TestCaseGenerationService testCaseGenerationService;
    
    @Autowired
    private JiraConnector jiraConnector;
    
    public ImpactAssessment generateImpactAssessment(String workflowId, String regulationId, String changeDescription) {
        // 1. Get workflow information
        Map<String, Object> workflowAnalysis = workflowAnalysisService.analyzeWorkflow(workflowId);
        Workflow workflow = (Workflow) workflowAnalysis.get("workflow");
        
        // 2. Create a new impact assessment
        ImpactAssessment assessment = new ImpactAssessment();
        assessment.setWorkflowId(workflowId);
        assessment.setRegulationId(regulationId);
        assessment.setCreationDate(new Date());
        assessment.setStatus("IN_PROGRESS");
        
        List<SystemImpact> systemImpacts = new ArrayList<>();
        List<String> requirements = new ArrayList<>();
        
        // 3. For each impacted system, analyze code impact
        for (String systemName : workflow.getImpactedSystems()) {
            Optional<System> systemOpt = systemRepository.findById(systemName);
            if (systemOpt.isPresent()) {
                System system = systemOpt.get();
                
                // 4. Identify impacted classes
                List<String> impactedClasses = codeImpactAnalysisService.identifyImpactedClasses(system.getId(), changeDescription);
                
                // 5. Generate test cases
                List<String> testCases = testCaseGenerationService.generateTestCases(impactedClasses, system.getId());
                
                // 6. Create JIRA ticket
                String jiraTicket = jiraConnector.createJiraTicket(system.getName(), 
                        "Regulatory Impact: " + changeDescription, 
                        "Impacted Classes: " + String.join(", ", impactedClasses));
                
                // 7. Create system impact object
                SystemImpact impact = new SystemImpact();
                impact.setSystemId(system.getId());
                impact.setSystemName(system.getName());
                impact.setImpactLevel(determineImpactLevel(impactedClasses.size()));
                impact.setImpactedClasses(impactedClasses);
                impact.setTestCases(testCases);
                impact.setJiraTicketId(jiraTicket);
                
                systemImpacts.add(impact);
                
                // 8. Generate requirements for this system
                List<String> systemRequirements = generateRequirementsForSystem(system, impactedClasses, changeDescription);
                requirements.addAll(systemRequirements);
            }
        }
        
        assessment.setImpactedSystems(systemImpacts);
        assessment.setGeneratedRequirements(requirements);
        assessment.setAutomationConfidence(calculateConfidence(systemImpacts));
        
        // 9. Save and return the impact assessment
        return impactAssessmentRepository.save(assessment);
    }
    
    private String determineImpactLevel(int classCount) {
        if (classCount > 20) return "HIGH";
        if (classCount > 5) return "MEDIUM";
        return "LOW";
    }
    
    private List<String> generateRequirementsForSystem(System system, List<String> impactedClasses, String changeDescription) {
        // Generate requirements based on system and impacted classes
        // This would use templates and NLP to create requirement statements
        List<String> requirements = new ArrayList<>();
        requirements.add("Update " + system.getName() + " to handle " + changeDescription);
        requirements.add("Modify " + impactedClasses.get(0) + " to implement new validation rules");
        requirements.add("Add logging for compliance tracking in affected components");
        return requirements;
    }
    
    private double calculateConfidence(List<SystemImpact> impacts) {
        // Calculate a confidence score for the automation
        // Based on historical accuracy for similar assessments
        return 0.90; // Default to 90% confidence
    }
}

// REST Controller for API
package com.trading.impactassessment.controller;

import com.trading.impactassessment.model.ImpactAssessment;
import com.trading.impactassessment.model.Workflow;
import com.trading.impactassessment.service.ImpactAssessmentService;
import com.trading.impactassessment.repository.WorkflowRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class ImpactAssessmentController {
    
    @Autowired
    private ImpactAssessmentService impactAssessmentService;
    
    @Autowired
    private WorkflowRepository workflowRepository;
    
    @GetMapping("/workflows")
    public ResponseEntity<List<Workflow>> getAllWorkflows() {
        return ResponseEntity.ok(workflowRepository.findAll());
    }
    
    @GetMapping("/workflows/{type}")
    public ResponseEntity<List<Workflow>> getWorkflowsByType(@PathVariable String type) {
        return ResponseEntity.ok(workflowRepository.findByWorkflowType(type));
    }
    
    @PostMapping("/impact-assessment")
    public ResponseEntity<ImpactAssessment> createImpactAssessment(@RequestBody Map<String, String> request) {
        String workflowId = request.get("workflowId");
        String regulationId = request.get("regulationId");
        String changeDescription = request.get("changeDescription");
        
        ImpactAssessment assessment = impactAssessmentService.generateImpactAssessment(
                workflowId, regulationId, changeDescription);
        
        return ResponseEntity.ok(assessment);
    }
    
    @GetMapping("/impact-assessment/{id}")
    public ResponseEntity<ImpactAssessment> getImpactAssessment(@PathVariable String id) {
        return impactAssessmentService.getImpactAssessmentById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}

// Configuration
package com.trading.impactassessment.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import org.springframework.data.mongodb.core.MongoTemplate;

@Configuration
public class AppConfig {
    
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
    
    @Bean
    public MongoClient mongoClient() {
        return MongoClients.create("mongodb://localhost:27017");
    }
    
    @Bean
    public MongoTemplate mongoTemplate() {
        return new MongoTemplate(mongoClient(), "tradingImpactAssessment");
    }
}

// Application Properties (application.properties)
// server.port=8080
// spring.data.mongodb.uri=mongodb://localhost:27017/tradingImpactAssessment
// logging.level.org.springframework=INFO
// logging.level.com.trading.impactassessment=DEBUG
