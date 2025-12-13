import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

import Home from './Home.jsx';
import NewHome from './NewHome.jsx';
import LoginPage from './LoginPage.jsx'
import PlaceholderImage from './PlaceholderImage.jsx'
import AboutPage from './AboutPage.jsx'

const router = createBrowserRouter([
  {
  path: '/',
  element: <LoginPage/>,
},
{
  path: '/Home',
  element: <NewHome/>,
},
{
  path: '/Map',
  element: <PlaceholderImage/>,
},
{
  path: '/About',
  element: <AboutPage/>,
},
]);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RouterProvider router={router}/>
  </StrictMode>,
)
