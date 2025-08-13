import { createBrowserRouter } from "react-router-dom";
import About from "../components/visitor/About";
import Cart from "../components/visitor/Cart";
import Category from "../components/visitor/Category";
import Checkout from "../components/visitor/Checkout";
import Home from "../components/visitor/Home";
import LoginAndSignup from "../components/visitor/LoginAndSignup";
import ProductDetail from "../components/visitor/ProductDetail";
import Store from "../components/visitor/Store";
import VisitorHomePage from "../components/visitor/VisitorHomePage";

export const router=createBrowserRouter([
    {
        path:"/",
        element:<VisitorHomePage/>,
        children:[
            { index: true, element: <Home /> },
            { path: "store/", element: <Store /> },
            { path: "store/:categorySlug/", element: <Store /> },
            { path: "products/:productSlug/", element: <ProductDetail /> },
            { path: "cart/", element: <Cart /> },
            { path: "checkout/", element: <Checkout /> },
            { path: "login/", element: <LoginAndSignup /> },
            { path: "about/", element: <About /> },
            
                ]

    }
])