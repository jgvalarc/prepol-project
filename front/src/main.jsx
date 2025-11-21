import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

import Home from './Home.jsx';
import LoginPage from './LoginPage.jsx'
// import MapAppBar from './MapAppBar.jsx';
import PlaceholderImage from './PlaceholderImage.jsx'
import Pickers from './Pickers.jsx'
import Test from './Test.jsx'

const router = createBrowserRouter([
  {
  path: '/',
  element: <Home/>,
},
{
  path: '/Login',
  element: <LoginPage/>,
},
{
  path: '/Map',
  element: <PlaceholderImage/>,
},
{
  path: '/Pickers',
  element: <Pickers/>,
},
{
  path: '/Test',
  element: <Test/>,
},
]);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RouterProvider router={router}/>
  </StrictMode>,
)
