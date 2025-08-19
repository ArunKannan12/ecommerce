import React, { useState } from 'react'
import { Modal,Button,Form,Spinner,Container,Card,Row,Col } from 'react-bootstrap'
import { toast } from 'react-toastify'
import { Link, useNavigate } from 'react-router-dom'
import {FaEye,FaEyeSlash} from 'react-icons/fa'
import axiosInstance from '../../api/axiosinstance'
const ChangePassword = () =>{
  const [form,setForm] = useState({
    current_password:'',
    new_password:'',
    re_new_password:''
  })
  const [showPassword, setShowPassword] = useState({
    current: false,
    new: false,
    confirm: false
  });
  const toggleVisibility = (field) => {
    setShowPassword((prev) => ({ ...prev, [field]: !prev[field] }));
  };
  const [loading,setLoading] = useState(false)
  const navigate = useNavigate();

  const handleChange = (e) =>{
    setForm((prev) => ({...prev, [e.target.name]: e.target.value}));
  };

  const handleSubmit =async (e) =>{
    e.preventDefault();

    if (form.new_password !== form.re_new_password) {
      toast.error("New password does not match")
      return
    }

    setLoading(true)
    setShowPassword(true)

    try{
      const res = await axiosInstance.post('auth/users/set_password/',form)
      navigate('/')
      toast.success("password reset successfull")

    }catch(error){
      const data = error.response?.data || {};
      const errorMsg =
      data.current_password?.[0] ||data.new_password?.[0] ||
      data.re_new_password?.[0] ||
      'Password reset failed';
      toast.error(errorMsg)
    }finally{
      setLoading(false)
    }
  }


const [backLoading, setBackLoading] = useState(false);
const handleBackClick = () => {
  setBackLoading(true);
  setTimeout(() => {
    navigate('/');
  },500); // Optional delay for spinner effect
};
  return (
     <Container fluid className="d-flex justify-content-center align-items-center py-4" style={{ minHeight: '100vh' }}>
      <Row className="w-100 justify-content-center">
        <Col xs={11} sm={9} md={7} lg={5} xl={4}>
          <Card className="p-4 shadow-sm border-0">
            <h4 className="mb-4 text-center">Reset Password</h4>
            <Form onSubmit={handleSubmit}>
              {/* Current Password */}
              <Form.Group controlId="currentPassword" className="mb-3 position-relative">
                <Form.Label>Current Password</Form.Label>
                <Form.Control
                  type={showPassword.current ? 'text' : 'password'}
                  name="current_password"
                  value={form.current_password}
                  onChange={handleChange}
                  required
                  minLength={8}
                />
                <span
                  onClick={() => toggleVisibility('current')}
                  style={{
                    position: 'absolute',
                    top: '38px',
                    right: '10px',
                    cursor: 'pointer',
                    color: '#6c757d'
                  }}
                >
                  {showPassword.current ? <FaEyeSlash /> : <FaEye />}
                </span>
              </Form.Group>

              {/* New Password */}
              <Form.Group controlId="newPassword" className="mb-3 position-relative">
                <Form.Label>New Password</Form.Label>
                <Form.Control
                  type={showPassword.new ? 'text' : 'password'}
                  name="new_password"
                  value={form.new_password}
                  onChange={handleChange}
                  required
                  minLength={8}
                />
                <span
                  onClick={() => toggleVisibility('new')}
                  style={{
                    position: 'absolute',
                    top: '38px',
                    right: '10px',
                    cursor: 'pointer',
                    color: '#6c757d'
                  }}
                >
                  {showPassword.new ? <FaEyeSlash /> : <FaEye />}
                </span>
              </Form.Group>

              {/* Confirm New Password */}
              <Form.Group controlId="reNewPassword" className="mb-4 position-relative">
                <Form.Label>Confirm New Password</Form.Label>
                <Form.Control
                  type={showPassword.confirm ? 'text' : 'password'}
                  name="re_new_password"
                  value={form.re_new_password}
                  onChange={handleChange}
                  required
                  minLength={8}
                />
                <span
                  onClick={() => toggleVisibility('confirm')}
                  style={{
                    position: 'absolute',
                    top: '38px',
                    right: '10px',
                    cursor: 'pointer',
                    color: '#6c757d'
                  }}
                >
                  {showPassword.confirm ? <FaEyeSlash /> : <FaEye />}
                </span>
              </Form.Group>

              <div className="d-grid">
                <Button variant="primary" type="submit" disabled={loading}>
                  {loading ? <Spinner animation="border" size="sm" /> : 'Reset Password'}
                </Button>
              </div>
            </Form>

            <div className="text-center mt-3">
              <a
                onClick={handleBackClick}
                className="text-decoration-none"
                role="button"
                style={{ cursor: 'pointer', color: '#0d6efd' }}
              >
                {backLoading ? (
                  <>
                    <Spinner animation="border" size="sm" /> Redirecting...
                  </>
                ) : (
                  '← Back to Profile'
                )}
              </a>
            </div>
          </Card>
        </Col>
      </Row>
    </Container>

  )
}
export default ChangePassword