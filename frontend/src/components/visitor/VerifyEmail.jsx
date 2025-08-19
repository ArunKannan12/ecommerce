import axios from "axios";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { useLocation } from "react-router-dom";
import { Container, Row, Col, Form, Button } from 'react-bootstrap';
import axiosInstance from "../../api/axiosinstance";


const VerifyEmail = () =>{
    const location = useLocation();  
    const preFilledEmail = location.state?.email || '';
    
    const [email, setEmail] = useState(preFilledEmail);
    const navigate = useNavigate()
    const handleResend = async () => {
        try {
            const response = await axiosInstance.post("auth/resend-activation/", { email });
            console.log(response.status);
            toast.success("Activation email resent successfully!");
        } catch (error) {
            console.error("Resend activation error:", error.response ? error.response.data : error.message);
            if (error.response) {
                        // Show exact backend error message if available
                toast.error(error.response.data.detail || "Failed to resend activation email.");
            } else {
                toast.error("Network error or server is unreachable.");
            }
}
    };
return (
        <Container className="py-5">
            <Row className="justify-content-center">
                <Col xs={12} sm={10} md={6} lg={4}>
                <div className="text-center bg-white p-4 rounded shadow-sm">
                    <h4 className="mb-3 text-primary">Email Verification</h4>
                    <p className="mb-4">Please check your inbox for an activation email.</p>

                    <Form.Control
                    type="email"
                    className="mb-3"
                    placeholder="Enter your email"
                    value={email}
                    required
                    disabled
                    onChange={(e) => setEmail(e.target.value)}
                    />

                    <Button
                    variant="warning"
                    onClick={handleResend}
                    className="w-100 mb-3"
                    >
                    Resend Activation Email
                    </Button>

                    <p className="mb-0">
                    Back to{' '}
                    <span
                        style={{ cursor: 'pointer', color: '#0d6efd', textDecoration: 'underline' }}
                        onClick={() => navigate('/')}
                    >
                        Login
                    </span>
                    </p>
                </div>
                </Col>
            </Row>
            </Container>
    );
};

export default VerifyEmail;