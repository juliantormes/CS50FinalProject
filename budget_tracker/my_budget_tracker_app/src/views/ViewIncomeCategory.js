import React, { useState, useEffect } from 'react';
import { Container, Typography, IconButton, Button, TextField } from '@mui/material';
import Header from '../components/Header';
import SidebarMenu from '../components/SidebarMenu';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Cancel';
import { useAuth } from '../hooks/useAuth';
import axiosInstance from '../api/axiosApi';
import '../styles/ViewIncomeCategory.css';

const ViewIncomeCategory = () => {
  const { logout } = useAuth();
  const [categories, setCategories] = useState([]);
  const [editingCategoryId, setEditingCategoryId] = useState(null);
  const [formData, setFormData] = useState({ name: '' });

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await axiosInstance.get('/api/income_categories/');
        setCategories(response.data);
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    };

    fetchCategories();
  }, []);

  const handleEditClick = (category) => {
    setEditingCategoryId(category.id);
    setFormData({ name: category.name });
  };

  const handleCancelClick = () => {
    setEditingCategoryId(null);
    setFormData({ name: '' });
  };

  const handleSaveClick = async (categoryId) => {
    try {
      const response = await axiosInstance.put(`/api/income_categories/${categoryId}/`, formData);
      if (response.status === 200) {
        const updatedCategories = categories.map((cat) =>
          cat.id === categoryId ? { ...cat, name: formData.name } : cat
        );
        setCategories(updatedCategories);
        setEditingCategoryId(null);
      } else {
        throw new Error('Failed to update category');
      }
    } catch (error) {
      console.error(error);
    }
  };

  const handleDeleteClick = async (categoryId) => {
    try {
      const response = await axiosInstance.delete(`/api/income_categories/${categoryId}/`);
      if (response.status === 204) {
        setCategories(categories.filter((cat) => cat.id !== categoryId));
      } else {
        throw new Error('Failed to delete category');
      }
    } catch (error) {
      console.error('Error deleting category:', error);
    }
  };

  const handleAddCategoryClick = () => {
    setEditingCategoryId('new');
    setFormData({ name: '' });
  };

  const handleNewCategorySave = async () => {
    try {
      const response = await axiosInstance.post('/api/income_categories/', formData);
      if (response.status === 201) {
        setCategories([...categories, response.data]);
        setEditingCategoryId(null);
        setFormData({ name: '' });
      } else {
        throw new Error('Failed to add category');
      }
    } catch (error) {
      console.error('Error adding category:', error);
    }
  };

  return (
    <div className="view-income-category">
      <div className="sidebar-container">
        <SidebarMenu />
      </div>
      <div className="content">
        <Header logout={logout} />
        <Container maxWidth="sm" className="container-top">
          <Typography variant="h4" gutterBottom>View Income Categories</Typography>
          <div className="category-list">
            {categories.map((category) => (
              <div key={category.id} className="category-item">
                {editingCategoryId === category.id ? (
                  <>
                    <TextField
                      value={formData.name}
                      onChange={(e) => setFormData({ name: e.target.value })}
                    />
                    <div className="actions">
                      <IconButton onClick={() => handleSaveClick(category.id)}>
                        <SaveIcon />
                      </IconButton>
                      <IconButton onClick={handleCancelClick}>
                        <CancelIcon />
                      </IconButton>
                    </div>
                  </>
                ) : (
                  <>
                    <span>{category.name}</span>
                    <div className="actions">
                      <IconButton onClick={() => handleEditClick(category)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton onClick={() => handleDeleteClick(category.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </div>
                  </>
                )}
              </div>
            ))}
            {editingCategoryId === 'new' && (
              <div className="category-item">
                <TextField
                  value={formData.name}
                  onChange={(e) => setFormData({ name: e.target.value })}
                />
                <div className="actions">
                  <IconButton onClick={handleNewCategorySave}>
                    <SaveIcon />
                  </IconButton>
                  <IconButton onClick={handleCancelClick}>
                    <CancelIcon />
                  </IconButton>
                </div>
              </div>
            )}
          </div>
          <div className="add-button-container">
            <Button
              variant="contained"
              color="primary"
              onClick={handleAddCategoryClick}
              className="add-button"
            >
              Add Income Category
            </Button>
          </div>
        </Container>
      </div>
    </div>
  );
};

export default ViewIncomeCategory;
