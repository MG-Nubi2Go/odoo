# Nybble User Management Module

## Overview

The **Nybble User Management** module is a custom Odoo extension that provides advanced
user management capabilities with enhanced security controls and granular access
permissions. This module is designed for Odoo 18.0 and follows Test-Driven Development
(TDD) principles.

## Features

### 🔐 Enhanced Security

- **Granular Access Control**: Custom user group with specific permissions
- **Administrative Restrictions**: Limits access to critical system configurations
- **Dynamic View Modifications**: Automatically restricts administrative groups
  visibility

### 👥 User Management

- **User Administration**: Complete user lifecycle management
- **Partner Token Fields**: Extended partner model with signup token capabilities
- **Email Template Management**: Integrated email template administration

### 🛡️ Security Groups

- **User Management Group**: Dedicated group for user administration
- **Restricted Permissions**: Read, write, and create permissions without deletion
  rights
- **Category Organization**: "Additional Permissions" category for better organization

## Installation

### Prerequisites

- Odoo 18.0 or higher
- PostgreSQL database
- Python 3.8+

### Installation Steps

1. **Clone or Download** the module to your Odoo addons path:

   ```bash
   cp -r nybble_user_management /path/to/odoo/addons/
   ```

2. **Update Module List** in Odoo:

   - Go to Apps → Update Apps List
   - Or restart Odoo server

3. **Install the Module**:

   - Search for "User Management" in the Apps menu
   - Click Install

4. **Configure Security**:
   - Assign users to the "User Management" group
   - Configure access rights as needed

## Module Structure

```
nybble_user_management/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── res_users.py
│   └── res_partner.py
├── security/
│   ├── ir.model.access.csv
│   └── user_group_views.xml
├── views/
│   ├── res_user_views.xml
│   └── user_management_menus.xml
├── tests/
│   ├── __init__.py
│   └── test_res_groups.py
└── static/
    └── description/
        └── icon.png
```

## Technical Documentation

### Models

#### GroupsView (res.groups)

**File**: `models/res_users.py`

Extends the `res.groups` model to modify user group views dynamically.

**Key Methods**:

- `_update_user_groups_view()`: Modifies the user groups view to exclude administration
  categories

**Features**:

- Dynamic XML view manipulation using lxml
- Restricts administrative group visibility
- Maintains original functionality while adding security layers

#### ResPartner (res.partner)

**File**: `models/res_partner.py`

Extends the `res.partner` model with signup token fields.

**New Fields**:

- `signup_token`: Computed field for registration tokens
- `signup_type`: Token type classification
- `signup_expiration`: Token expiration datetime

**Security**: All fields are restricted to ERP managers and user management groups.

### Security Configuration

#### User Management Group

- **Name**: "User Management"
- **Category**: "Additional Permissions"
- **Description**: Allows user administration without critical system access

#### Access Rights

- **Model**: res.users
- **Permissions**: Read (1), Write (1), Create (1), Delete (0)
- **Group**: nybble_user_management.group_user_management

### Views

#### Menu Structure

- **Main Menu**: "User Settings" (sequence: 1000)
- **Submenus**:
  - Users (redirects to base user management)
  - Email Templates (redirects to mail template management)

#### Form View Modifications

- Inherits base user form view
- Modifies partner_id field group restrictions
- Enhances accessibility for user management group

## Usage

### Assigning User Management Permissions

1. **Navigate to Settings** → Users & Companies → Users
2. **Select a user** to modify
3. **Add to Groups**: Select "User Management" from Additional Permissions
4. **Save** the user record

### Managing Users

1. **Access User Management**:

   - Go to User Settings → Users
   - Only visible to users with User Management group

2. **Create New Users**:

   - Click "Create" button
   - Fill in required fields
   - Assign appropriate groups
   - Save the record

3. **Edit Existing Users**:
   - Select user from list
   - Modify fields as needed
   - Save changes

### Email Template Management

1. **Access Templates**:
   - Go to User Settings → Email Templates
   - Manage email templates for user communications

## Testing

The module includes comprehensive unit tests following TDD principles.

### Running Tests

```bash
# Run specific test file
python -m pytest /path/to/odoo/addons/nybble_user_management/tests/

# Run with Odoo test framework
./odoo-bin -d your_database -i nybble_user_management --test-enable
```

### Test Coverage

- **Security Tests**: Verify access control and permissions
- **View Tests**: Validate dynamic view modifications
- **Group Tests**: Ensure proper group restrictions

## Configuration

### Customization Options

1. **Modify Group Permissions**:

   - Edit `security/ir.model.access.csv`
   - Adjust permission levels as needed

2. **Add New Menu Items**:

   - Modify `views/user_management_menus.xml`
   - Add new menuitem records

3. **Extend Partner Fields**:
   - Modify `models/res_partner.py`
   - Add new computed fields or methods

## Troubleshooting

### Common Issues

1. **Module Not Installing**:

   - Verify Odoo version compatibility (18.0+)
   - Check file permissions
   - Ensure all dependencies are installed

2. **Permission Errors**:

   - Verify user is assigned to User Management group
   - Check access rights configuration
   - Review security group assignments

3. **View Not Loading**:
   - Clear browser cache
   - Restart Odoo server
   - Check for XML syntax errors

### Debug Mode

Enable debug mode for detailed error information:

```bash
./odoo-bin -d your_database --dev=all
```

## Development

### Adding New Features

1. **Follow TDD Approach**:

   - Write tests first
   - Implement functionality
   - Verify test coverage

2. **Use unittest.mock**:

   - Isolate components for testing
   - Mock external dependencies
   - Follow Odoo testing conventions

3. **Maintain Code Standards**:
   - Follow PEP 8 for Python
   - Use descriptive names
   - Add comprehensive docstrings

### Code Style

- **Python**: PEP 8 compliant
- **XML**: Proper indentation and formatting
- **Documentation**: Google-style docstrings
- **Tests**: Arrange-Act-Assert pattern

## Dependencies

- **Odoo**: 18.0.1.0.0
- **Python**: 3.8+
- **PostgreSQL**: 12+
- **lxml**: For XML manipulation

## License

This module is licensed under LGPL-3.

## Support

For technical support or feature requests:

- **Author**: Nybble Group
- **Website**: https://www.nybblegroup.com
- **Documentation**: This README file

## Changelog

### Version 18.0.1.0.0

- Initial release
- User management group implementation
- Dynamic view modifications
- Partner token fields
- Comprehensive test suite

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow TDD approach
4. Add comprehensive tests
5. Submit pull request

---

**Note**: This module is designed for enterprise environments requiring enhanced user
management capabilities with strict security controls.
