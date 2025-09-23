# Design Guidelines for Unified Odoo Tools

## Core Principles

### 1. No Wrapper Policy
- **Avoid wrapper methods**: Use libraries directly whenever possible
- **Direct imports**: Import and use third-party libraries directly rather than creating abstraction layers
- **Examples**:
  - ❌ Bad: `def parse_yaml(file): return yaml.load(file)`
  - ✅ Good: Direct use of `yaml.load()` where needed
  - ❌ Bad: Creating a `GitWrapper` class around GitPython
  - ✅ Good: Using GitPython's `Repo` class directly

### 2. Simplicity First
- **No caching**: Avoid caching mechanisms at this stage to reduce complexity
- **Direct operations**: Read/compute data when needed rather than storing
- **Clear data flow**: Prioritize code clarity over micro-optimizations

### 3. Single Responsibility
- Each module should have one clear purpose
- Avoid mixing concerns (e.g., file I/O with business logic)

### 4. Composition Over Inheritance
- Prefer composition and dependency injection
- Use dataclasses for data structures
- Minimize class hierarchies

### 5. Explicit Over Implicit
- Clear, descriptive names for functions and variables
- Avoid magic numbers and strings
- Document complex logic inline

## Code Style

### Imports
- Group imports: stdlib, third-party, local
- Use absolute imports for clarity
- Import specific items rather than entire modules when practical

### Type Hints
- Use type hints for all function signatures
- Use `Optional` for nullable types
- Use `List`, `Dict`, `Set` from typing module

### Error Handling
- Use specific exceptions
- Log errors with context
- Fail fast on critical errors

### Data Structures
- Use dataclasses for structured data
- Use NamedTuples for immutable data
- Use Enums for fixed sets of values

## Architecture Patterns

### Command Pattern
- Each CLI command as a separate module
- Clear input/output contracts
- Validation at boundaries

### Repository Pattern
- Separate data access from business logic
- Use interfaces for data sources
- Mock-friendly design for testing

### Pipeline Pattern
- Composable processing steps
- Clear data flow
- Error handling at each stage

## Testing Guidelines

### Unit Tests
- Test pure functions in isolation
- Mock external dependencies
- Aim for 80% coverage minimum

### Integration Tests
- Test complete workflows
- Use fixtures for test data
- Test error scenarios

### Performance Tests
- Benchmark critical paths
- Monitor memory usage
- Test with realistic data sizes

## Documentation Standards

### Docstrings
- Google-style docstrings
- Document parameters and return types
- Include usage examples for complex functions

### Comments
- Explain why, not what
- Document complex algorithms
- Mark TODOs with issue numbers

### README Files
- Clear installation instructions
- Usage examples
- API reference links

## Dependency Management

### Direct Usage
- Use libraries as intended by their authors
- Avoid unnecessary abstractions
- Reference library documentation

### Version Pinning
- Pin major versions in requirements.txt
- Use >= for security updates
- Document breaking changes

### Minimal Dependencies
- Evaluate necessity of each dependency
- Prefer stdlib solutions when adequate
- Consider bundle size and compatibility